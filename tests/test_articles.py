"""Article HTTP contracts plus snapshot serialization and transaction conflict checks."""
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_article_service
from app.core.security import get_current_user_id
from app.infrastructure.neo4j.base import ConflictError, NotFoundError
from app.modules.articles.repository import ArticleRepositoryMixin
from app.modules.articles.service import ArticleService


class MemoryArticles:
    def __init__(self):
        self.rows = {}

    def save_article(self, article_id, user_id, payload):
        old = self.rows.get(article_id)
        if old and old['authorId'] != user_id:
            raise NotFoundError('Article not found')
        if payload['revision'] != (old['revision'] if old else 0):
            raise ConflictError('Stale revision')
        content = {k: payload[k] for k in ('title','subtitle','body','kind','book')}
        row = dict(old or {}, **content, articleId=article_id, authorId=user_id,
                   authorName='Ada', revision=payload['revision']+1,
                   updatedAt=datetime.now(timezone.utc).isoformat())
        row.setdefault('snapshot', None)
        row.setdefault('publishedAt', None)
        if payload['action'] == 'publish':
            row['snapshot'] = dict(content)
            row['publishedAt'] = row['updatedAt']
        elif payload['action'] == 'unpublish':
            row['snapshot'] = None
            row['publishedAt'] = None
        row['published'] = row['snapshot'] is not None
        self.rows[article_id] = row
        return dict(row)

    def get_article(self, article_id, owner_id=None):
        row=self.rows.get(article_id)
        if not row or (owner_id and row['authorId'] != owner_id) or (not owner_id and not row['published']):
            raise NotFoundError('Article not found')
        return dict(row) if owner_id else {**row, **row['snapshot']}

    def page_articles(self, page, size, owner_id=None, author_id=None):
        rows=[self.get_article(k,owner_id) for k,v in self.rows.items()
              if (v['authorId']==owner_id if owner_id else v['published'])
              and (not author_id or v['authorId']==author_id)]
        return rows[page*size:(page+1)*size],len(rows)

    def get_author(self,user_id):
        return {'userId':user_id,'name':'Ada','publishedCount':sum(r['published'] for r in self.rows.values() if r['authorId']==user_id), 'passwordHash':'never-public', 'email':'private@example.com'}


@pytest.fixture
def articles():
    repo=MemoryArticles()
    app.dependency_overrides[get_article_service]=lambda:ArticleService(repo)
    app.dependency_overrides[get_current_user_id]=lambda:'owner'
    yield TestClient(app),repo
    app.dependency_overrides.clear()


def save(client,id,revision=0,action='save',**kwargs):
    return client.put(f'/api/v1/articles/{id}',json={'revision':revision,'action':action,'title':'A story','body':'The first page.',**kwargs})


def test_private_draft_is_not_public_or_visible_to_another_owner(articles):
    client,_=articles;id=str(uuid4())
    assert save(client,id).status_code==200
    assert client.get('/api/v1/articles').json()['content']==[]
    assert client.get(f'/api/v1/articles/{id}').status_code==404
    assert client.get(f'/api/v1/me/articles/{id}').status_code==200
    app.dependency_overrides[get_current_user_id]=lambda:'other'
    assert client.get('/api/v1/me/articles').json()['content']==[]
    assert client.get(f'/api/v1/me/articles/{id}').status_code==404
    assert save(client,id,1).status_code==404


def test_publish_edit_and_unpublish_preserve_visibility_contract(articles):
    client,_=articles;id=str(uuid4())
    first=save(client,id,action='publish').json()
    assert first['revision']==1
    app.dependency_overrides.pop(get_current_user_id)
    assert client.get(f'/api/v1/articles/{id}').json()['body']=='The first page.'
    assert client.get('/api/v1/articles').json()['totalElements']==1
    app.dependency_overrides[get_current_user_id]=lambda:'owner'
    assert save(client,id,1,body='Unpublished edits').status_code==200
    assert client.get(f'/api/v1/articles/{id}').json()['body']=='The first page.'
    assert save(client,id,2,'publish',body='Unpublished edits').status_code==200
    assert client.get(f'/api/v1/articles/{id}').json()['body']=='Unpublished edits'
    assert save(client,id,3,'unpublish').status_code==200
    assert client.get(f'/api/v1/articles/{id}').status_code==404
    assert client.get(f'/api/v1/me/articles/{id}').json()['published'] is False


def test_stale_save_does_not_replace_newer_content(articles):
    client,repo=articles;id=str(uuid4())
    save(client,id)
    assert save(client,id,0,body='Overwrite').status_code==409
    assert repo.rows[id]['body']=='The first page.'


@pytest.mark.parametrize('payload',[{'title':'   '},{'body':'\n\t'}, {'kind':'Unknown'}, {'title':'x'*201}, {'body':'x'*100001}, {'revision':-1}, {'authorId':'other'}])
def test_invalid_publish_rejected(articles,payload):
    client,repo=articles
    result=client.put(f'/api/v1/articles/{uuid4()}',json={'revision':0,'action':'publish','title':'Title','body':'Body',**payload})
    assert result.status_code==400
    assert not repo.rows


def test_private_endpoints_require_auth_and_public_output_is_minimal(articles):
    client,_=articles;id=str(uuid4());save(client,id,action='publish')
    app.dependency_overrides.pop(get_current_user_id)
    assert save(client,str(uuid4())).status_code==401
    assert client.get('/api/v1/me/articles').status_code==401
    author=client.get('/api/v1/authors/owner').json()
    assert set(author)=={'userId','name','publishedCount'}
    summary=client.get('/api/v1/articles').json()['content'][0]
    assert 'body' not in summary and 'snapshot' not in summary
    assert client.get('/api/v1/articles?size=101').status_code==400


def test_repository_serialization_uses_published_snapshot_and_revision():
    content={'title':'Live','subtitle':'','body':'Public text','kind':'Article','book':''}
    row={'a':{'articleId':str(uuid4()),'ownerId':'owner','revision':7,'publishedRevision':2,
              'draftJson':json.dumps({**content,'body':'Private changes'}),'publishedJson':json.dumps(content),
              'updatedAt':'2026-10-02T00:00:00Z','publishedAt':'2026-10-01T00:00:00Z'},'authorName':'Ada'}
    public=ArticleRepositoryMixin._article_out(row)
    assert public['body']=='Public text' and public['revision']==2
    assert public['updatedAt']==row['a']['publishedAt']
    assert ArticleRepositoryMixin._article_out(row,private=True)['body']=='Private changes'


def test_repository_transaction_rejects_stale_revision_before_content_write():
    class Result:
        def __init__(self,value):self.value=value
        def single(self):return self.value
    class Transaction:
        queries=[]
        def run(self,query,**params):
            self.queries.append(query)
            if 'RETURN u.name' in query:return Result({'name':'Ada'})
            if 'MERGE' in query:return Result({'a':{'ownerId':'owner','revision':3}})
            pytest.fail('Stale request must not update content')
    class Session:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute_write(self,callback):return callback(Transaction())
    class Driver:
        def session(self):return Session()
    repo=ArticleRepositoryMixin();repo.driver=Driver();repo._article_schema_ready=True
    with pytest.raises(ConflictError):
        repo.save_article(str(uuid4()),'owner',{'title':'New','subtitle':'','body':'Body','kind':'Article','book':'','revision':2,'action':'save'})
    assert 'SET a._writeLock = true' in Transaction.queries[1]
