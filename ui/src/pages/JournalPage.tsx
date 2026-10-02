import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, Download, Eye, PenLine, Plus, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { articlesApi, errorMessage, type Article, type ArticleContent, type ArticleAction } from '../api/articles';
import { PageNav, LoadState } from '../components/Editorial';
import { StoryBody } from '../components/StoryBody';

type LegacyDraft = ArticleContent & { id: string; updatedAt: string };
const blank: ArticleContent = { title:'', subtitle:'', body:'', kind:'Article', book:'' };
const storageKey = (userId: string | null) => `novelist:drafts:v1:${userId ?? 'guest'}`;
function readLegacy(key: string): { drafts: LegacyDraft[]; error: boolean } {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(key) || '[]');
    if (!Array.isArray(value) || !value.every(d => d && typeof d.id === 'string' && typeof d.updatedAt === 'string' && validContent(d))) return {drafts:[],error:true};
    return {drafts:value,error:false};
  } catch { return {drafts:[],error:true}; }
}
function localDrafts(userId: string | null) {
  const legacy=readLegacy(storageKey(userId));
  try {
    const prefix=`novelist:recovery:${userId}:`;
    for (let i=0;i<localStorage.length;i++) {
      const key=localStorage.key(i);
      if (!key?.startsWith(prefix)) continue;
      const value:unknown=JSON.parse(localStorage.getItem(key)||'null');
      const id=key.slice(prefix.length);
      if (validContent(value) && !legacy.drafts.some(d=>d.id===id)) legacy.drafts.push({...value,id,updatedAt:new Date().toISOString()});
    }
  } catch { legacy.error=true; }
  return legacy;
}
function validContent(value: unknown): value is ArticleContent {
  if (!value || typeof value !== 'object') return false;
  const d=value as ArticleContent;
  return ['title','subtitle','body','book'].every(k=>typeof d[k as keyof ArticleContent] === 'string') && (d.kind === 'Article' || d.kind === 'Book review');
}
function contentOf(article: ArticleContent): ArticleContent {
  return {title:article.title,subtitle:article.subtitle,body:article.body,kind:article.kind,book:article.book};
}
const words = (body: string) => body.trim() ? body.trim().split(/\s+/).length : 0;

export function JournalPage() {
  const {userId}=useAuth(); const [page,setPage]=useState(0);
  const local=localDrafts(userId);
  const query=useQuery({queryKey:['articles','mine',userId,page],queryFn:()=>articlesApi.mine(page)});
  return <section className="journal-page"><div className="journal-heading"><div><p className="eyebrow">A collection of your thoughts</p><h1>Your words,<br/><em>in the making.</em></h1><p className="intro-copy">Private drafts and published stories, all in one place.</p></div><Link className="ink-button" to="/write"><Plus size={16}/>Start a draft</Link></div><div className="section-rule"><span>My stories</span><span>Saved to your account</span></div>{query.isPending || query.isError ? <LoadState loading={query.isPending} error={query.isError} retry={()=>query.refetch()}/> : query.data.content.length ? <><div className="draft-list">{query.data.content.map(d=><Link key={d.articleId} to={`/write/${d.articleId}`} className="draft-row"><div><p className="eyebrow">{d.kind} · {d.published ? 'Published · editable draft' : 'Private draft'}</p><h2>{d.title || 'Untitled story'}</h2><p>{d.subtitle || 'A blank page, full of possibilities.'}</p><small>Updated {new Date(d.updatedAt).toLocaleDateString()}</small></div><ArrowRight size={22}/></Link>)}</div><PageNav page={page} total={query.data.totalPages} onPage={setPage}/></> : <div className="journal-empty"><PenLine size={30}/><h2>Something worth saying<br/>starts with a single sentence.</h2><p>Your drafts stay private until you publish.</p><Link className="ink-button" to="/write">Write your first story <ArrowRight size={16}/></Link></div>}
    {(local.error || local.drafts.length>0) && <section className="legacy-drafts"><h2>From your browser notebook</h2><p>Earlier local drafts are preserved. Open one and save it to your account; the original browser copy remains here as a backup.</p>{local.error ? <p role="alert">Browser drafts couldn’t be read. Existing data has not been changed.</p> : local.drafts.map(d=><Link className="draft-row" key={d.id} to={`/write/${d.id}`}><span>{d.title || 'Untitled local draft'}</span><ArrowRight size={16}/></Link>)}</section>}
  </section>;
}

export function WriterPage() {
  const {draftId}=useParams(); const {userId}=useAuth();
  const query=useQuery({queryKey:['articles','draft',userId,draftId],queryFn:async()=>{
    try { return {article:await articlesApi.draft(draftId!),legacy:null}; }
    catch(error) {
      if ((error as {response?:{status:number}}).response?.status === 404) {
        const legacy=localDrafts(userId).drafts.find(d=>d.id===draftId);
        if (legacy) return {article:null,legacy};
      }
      throw error;
    }
  },enabled:!!draftId,retry:false});
  if (draftId && (query.isPending || query.isError)) return <LoadState loading={query.isPending} error={query.isError} retry={()=>query.refetch()}/>;
  return <DraftEditor key={`${userId}:${draftId || 'new'}`} userId={userId} initial={query.data?.article || null} legacy={query.data?.legacy || null}/>;
}
function DraftEditor({userId,initial,legacy}:{userId:string|null;initial:Article|null;legacy:LegacyDraft|null}) {
  const navigate=useNavigate(); const cache=useQueryClient(); const bodyRef=useRef<HTMLTextAreaElement>(null);
  const [id]=useState(()=>initial?.articleId || legacy?.id || crypto.randomUUID());
  const backupKey=`novelist:recovery:${userId}:${id}`;
  const [recovery]=useState<ArticleContent|null>(()=>{
    try { const value:unknown=JSON.parse(localStorage.getItem(backupKey)||'null'); return validContent(value) ? value : null; } catch { return null; }
  });
  const [draft,setDraft]=useState<ArticleContent>(()=>contentOf(initial || legacy || blank));
  const [revision,setRevision]=useState(initial?.revision || 0);
  const [published,setPublished]=useState(initial?.published || false);
  const [dirty,setDirty]=useState(!!legacy);
  const [preview,setPreview]=useState(false); const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState(initial ? 'Saved to your account' : legacy ? 'Local draft — save to your account when ready' : 'New draft');
  const [error,setError]=useState(''); const [showRecovery,setShowRecovery]=useState(!!recovery);
  useEffect(()=>{
    const guard=(event:BeforeUnloadEvent)=>{if(dirty){event.preventDefault();event.returnValue='';}};
    window.addEventListener('beforeunload',guard);return()=>window.removeEventListener('beforeunload',guard);
  },[dirty]);
  const update=(patch:Partial<ArticleContent>)=>{
    const next={...draft,...patch};setDraft(next);setDirty(true);setError('');
    try {localStorage.setItem(backupKey,JSON.stringify(next));setNotice('Unsaved changes · recovery copy on this device');}
    catch {setNotice('Unsaved changes · browser backup unavailable');}
  };
  const save=async(action:ArticleAction)=>{
    setBusy(true);setError('');
    try {
      const saved=await articlesApi.save(id,draft,revision,action);
      setRevision(saved.revision);setPublished(saved.published);setDirty(false);setShowRecovery(false);
      setNotice(action==='publish'?'Published — your story is live':action==='unpublish'?'Unpublished — visible only to you':'Saved to your account');
      try {localStorage.removeItem(backupKey);} catch { /* Server save is still successful. */ }
      cache.setQueryData(['articles','draft',userId,id],{article:saved,legacy:null});
      void cache.invalidateQueries({queryKey:['articles']});void cache.invalidateQueries({queryKey:['author',userId]});
      if (!initial && !legacy) navigate(`/write/${id}`,{replace:true});
    } catch(err) {setError(errorMessage(err,'Couldn’t save. Keep this page open or export your draft, then try again.'));}
    finally {setBusy(false);}
  };
  const format=(before:string,after='')=>{
    const input=bodyRef.current; if(!input)return;
    const start=input.selectionStart,end=input.selectionEnd;
    update({body:draft.body.slice(0,start)+before+(draft.body.slice(start,end)||'Your words')+after+draft.body.slice(end)});
    input.focus();
  };
  const exportDraft=()=>{
    const text=`# ${draft.title||'Untitled story'}\n\n${draft.subtitle}\n\n${draft.book?`Book: ${draft.book}\n\n`:''}${draft.body}\n`;
    const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=`${draft.title.replace(/[^a-zA-Z0-9 -]/g,'').trim().slice(0,70)||'untitled-story'}.md`;
    document.body.append(a);a.click();a.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  return <section className="writer-page"><div className="writer-toolbar"><Link className="text-link" to="/journal"><ArrowLeft size={16}/>My journal</Link><span className="save-state" role="status">{notice}</span><div className="writer-actions"><button className="outline-button" onClick={()=>setPreview(!preview)}>{preview?<PenLine size={15}/>:<Eye size={15}/>} {preview?'Keep writing':'Preview'}</button><button className="outline-button" disabled={busy} onClick={()=>save('save')}><Save size={15}/>{busy?'Saving…':'Save draft'}</button><button className="ink-button" disabled={busy||!draft.title.trim()||!draft.body.trim()} onClick={()=>save('publish')}>{published?'Publish changes':'Publish story'}</button></div></div>
    {error && <div className="notice-error" role="alert">{error} <span>Your text has not been replaced. Export a copy before reloading a newer server version.</span></div>}
    {showRecovery && recovery && <div className="recovery-notice"><span>A local recovery copy is available. Restoring it replaces the editor text, not the published story.</span><button className="outline-button" disabled={busy} onClick={()=>{update(recovery);setShowRecovery(false);}}>Restore local copy</button><button className="text-link" onClick={()=>setShowRecovery(false)}>Keep server version</button></div>}
    <div className="writing-paper"><div className="paper-topline"><span className="eyebrow">{preview?'Reading preview':published?'Working draft · published version stays unchanged':'Private working draft'}</span><span>{words(draft.body)} words · {Math.max(1,Math.ceil(words(draft.body)/200))} min read</span></div>{preview?<article className="draft-preview"><p className="eyebrow">{draft.kind}{draft.book?` / ${draft.book}`:''}</p><h1>{draft.title||'Untitled story'}</h1><p className="preview-subtitle">{draft.subtitle}</p><StoryBody text={draft.body||'Your story will appear here.'}/></article>:<fieldset disabled={busy} className="writer-fields"><div className="draft-options"><label>Writing a<select value={draft.kind} onChange={e=>update({kind:e.target.value as ArticleContent['kind']})}><option>Article</option><option>Book review</option></select></label>{draft.kind==='Book review'&&<label>About the book<input maxLength={300} placeholder="Book title and author" value={draft.book} onChange={e=>update({book:e.target.value})}/></label>}</div><label className="sr-only" htmlFor="story-title">Story title</label><textarea id="story-title" className="story-title" rows={2} maxLength={200} placeholder="Give your story a title…" value={draft.title} onChange={e=>update({title:e.target.value})}/><label className="sr-only" htmlFor="story-subtitle">Subtitle</label><textarea id="story-subtitle" rows={2} maxLength={500} className="story-subtitle" placeholder="A few words to invite your reader in." value={draft.subtitle} onChange={e=>update({subtitle:e.target.value})}/><div className="format-toolbar" aria-label="Text formatting"><button type="button" onClick={()=>format('**','**')}>Bold</button><button type="button" onClick={()=>format('*','*')}>Italic</button><button type="button" onClick={()=>format('\n\n## ')}>Heading</button><button type="button" onClick={()=>format('\n\n> ')}>Quote</button><button type="button" onClick={()=>format('\n\n- ')}>List</button><span>Markdown · Preview to read</span></div><label className="sr-only" htmlFor="story-body">Story body</label><textarea ref={bodyRef} id="story-body" className="story-body" maxLength={100000} placeholder="Begin with what stayed with you…" value={draft.body} onChange={e=>update({body:e.target.value})}/></fieldset>}
    <div className="paper-footnote">Save draft stores your private working copy in your account. Publish makes the current version available to everyone, including signed-out visitors. Long-form book reviews here are separate from star ratings.<div className="paper-actions"><button className="text-link" onClick={exportDraft}><Download size={14}/>Export Markdown</button>{published&&<><Link className="text-link" to={`/articles/${id}`}>View published story <ArrowRight size={14}/></Link><button className="text-link" disabled={busy} onClick={()=>save('unpublish')}>Unpublish story</button></>}</div></div></div></section>;
}
