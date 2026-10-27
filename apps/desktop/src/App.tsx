import { useCallback, useEffect, useRef, useState } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { Plus, Save, Play, Undo2, Redo2, Copy, Trash2, Upload, Layers3, Search, PanelLeftClose, ChevronDown, Cloud, HardDrive, X, Image, Film, AudioLines, UserRound, MapPin, FolderOpen, AlertCircle, Settings2, Download } from 'lucide-react';
import { api, ApiError, connectSession, json, mediaUrl, downloadUrl, thumbnailUrl } from './api';
import { useStudio } from './store';
import { Canvas } from './Canvas';
import { Inspector } from './Inspector';
import { Timeline } from './Timeline';
import { Settings } from './Settings';
import { createProjectLoadGate } from './projectLoad';
import { mergeTaskRefresh } from './taskRefresh';
import { AssetRename } from './AssetRename';
import { collectShotReferenceIds } from './shotReferences';
import type { AppSettings, Config, LocationDraft, CharacterDraft, Asset, CanvasDoc, CostEstimate, Definition, ExportJob, GenerationOptions, PeopleDoc, Profile, Project, Provider, Shot, Task, TimelineDoc } from './types';

const emptyTimeline: TimelineDoc = { clips: [], audio: [], subtitles: [], fps: 30, width: 1080, height: 1920, version: 1 };
const emptyPeople: PeopleDoc = { characters: [], locations: [], shots: [], version: 1 };

export default function App() {
  const studio = useStudio();
  const [projects, setProjects] = useState<Project[]>([]), [project, setProject] = useState<Project>();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [generationOptions, setGenerationOptions] = useState<GenerationOptions>({ workflows: [], textServices: [] });
  const [timeline, setTimeline] = useState<TimelineDoc>(emptyTimeline), [people, setPeople] = useState<PeopleDoc>(emptyPeople);
  const [tab, setTab] = useState('nodes'), [search, setSearch] = useState('');
  const [message, setMessage] = useState(''), [fatal, setFatal] = useState(''), [ready, setReady] = useState(false);
  const [saving, setSaving] = useState(false), [newProject, setNewProject] = useState(false), [name, setName] = useState('');
  const [saveError, setSaveError] = useState('');
  const [exportJob, setExportJob] = useState<ExportJob>(), [sidebar, setSidebar] = useState(true);
  const [profileEdit, setProfileEdit] = useState<{ type: 'characters' | 'locations'; profile: Profile }>();
  const [previewAsset, setPreviewAsset] = useState<Asset>();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsTab, setSettingsTab] = useState('services');
  const [canvasPreferences, setCanvasPreferences] = useState({ canvasHidePreviews: true, canvasPreviewThreshold: 50 });
  const [runStage, setRunStage] = useState(''), [taskActivitySignal, setTaskActivitySignal] = useState(0);
  const runLock = useRef(false);
  const projectLoadGate = useRef(createProjectLoadGate());
  const activeProject = useRef<Project>(undefined), projectLoading = useRef(false);
  useEffect(() => { if (project) activeProject.current = project; }, [project]);
  const [recordEdit, setRecordEdit] = useState<{ type: 'episodes' | 'scenes'; record: { id: string; name: string; script: string; episodeId?: string; locationId?: string } }>();
  const pid = useRef(''), timelineRef = useRef(timeline), peopleRef = useRef(people);
  const timelineDirty = useRef(false), peopleDirty = useRef(false), saveChain = useRef(Promise.resolve());
  const fileInput = useRef<HTMLInputElement>(null);
  const projectInput = useRef<HTMLInputElement>(null), templateInput = useRef<HTMLInputElement>(null);
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const notice = useCallback((text: string) => {
    clearTimeout(noticeTimer.current);
    setMessage(text);
    noticeTimer.current = text ? setTimeout(() => { setMessage(''); noticeTimer.current = undefined; }, 5000) : undefined;
  }, []);
  useEffect(() => () => clearTimeout(noticeTimer.current), []);
  useEffect(() => {
    const downloaded = (event: Event) => {
      const detail = (event as CustomEvent<{ status: string; path?: string }>).detail;
      if (detail?.status === 'completed') notice(`已保存到：${detail.path || '系统下载目录'}`);
      else if (detail?.status === 'failed') notice('下载失败，请检查下载目录权限和磁盘空间后重试');
      else if (detail?.status === 'started') notice('正在保存到下载目录…');
    };
    window.addEventListener('canvas-download', downloaded);
    return () => window.removeEventListener('canvas-download', downloaded);
  }, [notice]);
  const act = useCallback(async (action: () => Promise<unknown>) => { try { await action(); } catch (e) { notice(e instanceof Error ? e.message : String(e)); } }, [notice]);
  function captureProject() {
    const id = pid.current, epoch = projectLoadGate.current.snapshot();
    return { id, current: () => !!id && !projectLoading.current && pid.current === id && projectLoadGate.current.isLatest(epoch) };
  }
  function changeTimeline(doc: TimelineDoc) { timelineRef.current = doc; timelineDirty.current = true; setTimeline(doc); }
  function changePeople(doc: PeopleDoc) { peopleRef.current = doc; peopleDirty.current = true; setPeople(doc); }
  function editProfile(patch: Partial<Profile>) { setProfileEdit(current => current ? { ...current, profile: { ...current.profile, ...patch } } : undefined); }
  function refreshProviders() { void act(async () => {
    const [available, options, preferences] = await Promise.all([api<Provider[]>('/providers'), api<GenerationOptions>('/generation-options'), api<AppSettings>('/settings')]);
    setCanvasPreferences(preferences);
    setProviders(available); setGenerationOptions(options);
  }); }
  async function downloadProject(template = false) {
    await save(); if (!project) return;
    const response = await fetch(`/api/v1/projects/${project.id}/${template ? 'template' : 'archive'}`);
    if (!response.ok) throw new Error((await response.json()).message || '项目导出失败');
    const url = URL.createObjectURL(await response.blob()), link = document.createElement('a');
    link.href = url; link.download = project.name.replace(/[\\/:*?"<>|]/g, '_') + (template ? '.canvas-template.json' : '.canvas.zip');
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    notice(template ? '画布模板已导出，不包含素材或凭据' : '完整项目包已导出，包含媒体及校验清单');
  }

  const save = useCallback(async () => {
    const pending = saveChain.current.catch(() => {}).then(async () => {
      const id = pid.current; if (!id) return; setSaving(true);
      try {
        const s = useStudio.getState();
        if (s.edits !== s.savedEdits) {
          const canvas: CanvasDoc = { nodes: s.nodes.map(n => ({ ...n, selected: false })), edges: s.edges, viewport: s.viewport, version: s.version };
          const result = await api<CanvasDoc>(`/canvases/${id}`, { ...json('PUT', canvas), headers: { 'If-Match': String(s.version) } });
          if (id === pid.current) useStudio.setState({ version: result.version, savedEdits: s.edits });
        }
        if (timelineDirty.current && id === pid.current) {
          const current = timelineRef.current;
          const result = await api<TimelineDoc>(`/projects/${id}/timeline`, json('PUT', current));
          if (id === pid.current) {
            timelineDirty.current = timelineRef.current !== current;
            timelineRef.current = { ...timelineRef.current, version: result.version }; setTimeline(timelineRef.current);
          }
        }
        if (peopleDirty.current && id === pid.current) {
          const current = peopleRef.current;
          const result = await api<PeopleDoc>(`/projects/${id}/people`, json('PUT', current));
          if (id === pid.current) { peopleDirty.current = peopleRef.current !== current; peopleRef.current = { ...peopleRef.current, version: result.version }; setPeople(peopleRef.current); }
        }
        if (id === pid.current) setSaveError('');
      } catch (error) {
        if (id === pid.current) setSaveError(error instanceof Error ? error.message : String(error));
        throw error;
      } finally { setSaving(false); }
    });
    saveChain.current = pending;
    return pending;
  }, []);

  const openProject = useCallback(async (id: string) => {
    const request = projectLoadGate.current.begin();
    projectLoading.current = true;
    setProject(undefined);
    setProfileEdit(undefined); setRecordEdit(undefined); setPreviewAsset(undefined);
    let loaded: [Project, CanvasDoc, Asset[], TimelineDoc, PeopleDoc];
    try {
      await save();
      if (!projectLoadGate.current.isLatest(request)) return;
      loaded = await Promise.all([
        api<Project>(`/projects/${id}`), api<CanvasDoc>(`/canvases/${id}`), api<Asset[]>(`/projects/${id}/assets`),
        api<TimelineDoc>(`/projects/${id}/timeline`), api<PeopleDoc>(`/projects/${id}/people`),
      ]);
    } catch (error) {
      if (!projectLoadGate.current.isLatest(request)) return;
      projectLoading.current = false;
      setProject(activeProject.current);
      throw error;
    }
    if (!projectLoadGate.current.isLatest(request)) return;
    const [p, c, a, t, profiles] = loaded;
    projectLoading.current = false; activeProject.current = p;
    pid.current = id; useStudio.getState().load(c); useStudio.setState({ assets: a }); setProject(p);
    timelineRef.current = t; peopleRef.current = profiles; timelineDirty.current = false; peopleDirty.current = false;
    setTimeline(t); setPeople(profiles); setSaveError(''); setExportJob(undefined); localStorage.setItem('canvas-last-project', id);
  }, [save]);

  useEffect(() => { void (async () => {
    try {
      await connectSession();
      setCanvasPreferences(await api<AppSettings>('/settings'));
      const [ps, defs, available, options] = await Promise.all([api<Project[]>('/projects'), api<Record<string, Definition>>('/definitions'), api<Provider[]>('/providers'), api<GenerationOptions>('/generation-options')]);
      setProjects(ps); useStudio.setState({ definitions: defs }); setProviders(available); setGenerationOptions(options); setReady(true);
      const last = localStorage.getItem('canvas-last-project');
      if (ps.length) await openProject(ps.find(p => p.id === last)?.id || ps[0].id);
      else setNewProject(true);
    } catch (e) { setFatal(e instanceof Error ? e.message : String(e)); }
  })(); }, [openProject]);

  useEffect(() => {
    if (!project) return;
    const id = project.id;
    let stopped = false, retries = 0;
    let timeout: ReturnType<typeof setTimeout>;
    const attempt = async () => {
      if (stopped || pid.current !== id || projectLoading.current) return;
      const current = useStudio.getState();
      if (current.edits === current.savedEdits && !timelineDirty.current && !peopleDirty.current) return;
      try { await save(); }
      catch (error) {
        if (stopped || pid.current !== id) return;
        if (error instanceof ApiError && error.retryable && retries < 3) {
          timeout = setTimeout(() => void attempt(), 2000 * 2 ** retries++);
        }
      }
    };
    timeout = setTimeout(() => void attempt(), 1000);
    return () => { stopped = true; clearTimeout(timeout); };
  }, [studio.edits, timeline, people, project, save]);

  useEffect(() => {
    if (!project) return;
    const id = project.id;
    let stopped = false, polling = false, disconnected = false;
    let controller: AbortController | undefined;
    const refresh = async () => {
      if (stopped || document.hidden || polling) return; polling = true;
      const request = new AbortController(); controller = request;
      try {
        const [tasks, assets] = await Promise.all([api<Task[]>(`/projects/${id}/tasks`, { signal: request.signal }), api<Asset[]>(`/projects/${id}/assets`, { signal: request.signal })]);
        if (!stopped && pid.current === id) {
          useStudio.setState(state => mergeTaskRefresh(state, tasks, assets));
          if (disconnected) notice('连接已恢复，任务和素材已更新');
          disconnected = false;
        }
      } catch (e) {
        if (!stopped && !disconnected) { disconnected = true; notice('连接中断，将自动重连。' + (e instanceof Error ? e.message : '')); }
      }
      finally { request.abort(); controller = undefined; polling = false; }
    };
    void refresh(); const timer = setInterval(() => void refresh(), 2000);
    const visible = () => { if (!document.hidden) void refresh(); };
    document.addEventListener('visibilitychange', visible);
    return () => { stopped = true; controller?.abort(); clearInterval(timer); document.removeEventListener('visibilitychange', visible); };
  }, [project?.id, notice]);

  useEffect(() => {
    if (!exportJob || !['queued', 'running'].includes(exportJob.status)) return;
    const scope = captureProject();
    let stopped = false, polling = false;
    const timer = setInterval(() => void act(async () => {
      if (stopped || polling || !scope.current()) return;
      polling = true;
      try {
        const result = await api<ExportJob>(`/exports/${exportJob.id}`);
        if (!stopped && scope.current()) setExportJob(result);
      } finally { polling = false; }
    }), 1500);
    return () => { stopped = true; clearInterval(timer); };
  }, [exportJob, act]);

  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (projectLoading.current) return;
      if ((event.target as HTMLElement)?.closest('input,textarea,select,[contenteditable]')) return;
      const s = useStudio.getState();
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); void act(save); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? s.redo() : s.undo(); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'd') { event.preventDefault(); s.duplicate(); }
      if (event.key === 'Delete' || event.key === 'Backspace') { event.preventDefault(); s.remove(); }
      if (event.key === 'Escape') { setPreviewAsset(undefined); setProfileEdit(undefined); setRecordEdit(undefined); setNewProject(false); setSettingsOpen(false); }
    };
    const beforeUnload = (e: BeforeUnloadEvent) => { const s = useStudio.getState(); if (s.edits !== s.savedEdits || timelineDirty.current || peopleDirty.current) { e.preventDefault(); } };
    window.addEventListener('keydown', key); window.addEventListener('beforeunload', beforeUnload);
    return () => { window.removeEventListener('keydown', key); window.removeEventListener('beforeunload', beforeUnload); };
  }, [act, save]);

  async function createProject() {
    const p = await api<Project>('/projects', json('POST', { name }));
    setProjects(ps => [p, ...ps]); await openProject(p.id); setNewProject(false); setName(''); notice('项目已创建，所有素材保存在本机');
  }

  function run(ids: string[], force = false) {
    if (runLock.current || !project) return;
    runLock.current = true;
    const projectId = project.id;
    setRunStage('保存中…');
    void act(async () => { try {
    await save();
    if (pid.current !== projectId) return;
    setRunStage('检查配置…');
    const [estimate, preferences] = await Promise.all([
      api<CostEstimate>('/runs/estimate', json('POST', { projectId, nodeIds: ids, force })),
      api<{ confirmGenerationCost?: boolean }>('/settings'),
    ]);
    if (pid.current !== projectId) return;
    const anyCloud = estimate.quotes.some(q => q.provider !== 'comfyui' && q.basis !== 'local');
    if (anyCloud && project.settings.cloudEnabled && preferences.confirmGenerationCost !== false) {
      const amounts = Object.entries(estimate.totals).map(([currency, value]) => `${value} ${currency}`).join(' / ') || '未配置价格';
      if (!confirm(`即将运行 ${estimate.nodeIds.length} 个节点。提示词和引用素材将上传至 RunningHub / 文本服务。\n预估：${amounts}${estimate.unknownCount ? `，${estimate.unknownCount} 项费用未知` : ''}。预估不代表结算，服务商可能收费。是否提交？`)) return;
    }
    setRunStage('提交中…');
    const run = await api<{ id: string }>('/runs', json('POST', { projectId, nodeIds: ids, force }));
    if (pid.current !== projectId) return;
    setTaskActivitySignal(value => value + 1);
    notice('任务已进入队列，可在任务中心查看');
    let submitted: { tasks: Task[] };
    try { submitted = await api<{ tasks: Task[] }>(`/runs/${run.id}`); }
    catch { notice('任务已提交，详情暂未读取；将自动刷新，请勿重复提交'); return; }
    if (pid.current !== projectId) return;
    // 此次已提交当前参数；之后继续编辑会重新标为 dirty。
    useStudio.setState(s => ({ tasks: [...submitted.tasks, ...s.tasks.filter(t => !submitted.tasks.some(next => next.id === t.id))], nodes: s.nodes.map(n => {
      const task = submitted.tasks.find(t => t.node_id === n.id);
      return task && task.created_at >= Number(n.data.modifiedAt || 0) ? { ...n, data: { ...n.data, status: task.status } } : n;
    }) }));
    } finally { runLock.current = false; setRunStage(''); } });
  }

  function addClip(asset: Asset, title: string, seconds: number) {
    changeTimeline({ ...timelineRef.current, clips: [...timelineRef.current.clips, { id: crypto.randomUUID(), assetId: asset.id, title, durationMs: seconds * 1000, inMs: 0, approved: true }] });
    notice('已批准此版本并加入时间线');
  }

  function importCharacters(characters: CharacterDraft[], taskId: string, generate = false, generationConfig?: Config) {
    if (generate && runLock.current) return;
    generationConfig = { ...generationConfig, visualStyle: generationConfig?.visualStyle || useStudio.getState().tasks.find(task => task.id === taskId)?.snapshot.config.visualStyle };
    const selectedId = useStudio.getState().nodes.find(node => node.selected)?.id;
    const current = peopleRef.current;
    const existing = new Set(current.characters.map(character => character.sourceKey));
    const additions = characters.map((character, index) => ({ ...character, id: crypto.randomUUID(), sourceKey: `${taskId}:${index}` }))
      .filter(character => !existing.has(character.sourceKey));
    if (!additions.length && !generate) { notice('这次任务的角色已确认，可在角色库中编辑'); return; }
    const baseY = Math.max(0, ...useStudio.getState().nodes.map(node => node.position.y + (node.measured?.height || 350))) + 80;
    const targets = characters.map((_, index) => [...current.characters, ...additions].find(character => character.sourceKey === `${taskId}:${index}`)!);
    const ids = targets.map((character, index) => useStudio.getState().nodes.find(node => node.data.kind === 'image.character' && node.data.config.characterId === character.id)?.id || useStudio.getState().add('image.character', { x: 140 + index % 3 * 330, y: baseY + Math.floor(index / 3) * 400 }, {
      provider: generationConfig?.provider, workflowId: generationConfig?.workflowId, referenceIds: generationConfig?.referenceIds,
      characterId: character.id,
      visualStyle: generationConfig?.visualStyle,
      prompt: [`角色三视图设定：${character.name}`, character.description, character.appearance && `外貌：${character.appearance}`,
        character.wardrobe && `服装：${character.wardrobe}`, character.restrictions && `限制：${character.restrictions}`,
        '同一角色的正面、侧面、背面，全身等比例展示在一张图中，简洁背景，不添加文字。'].filter(Boolean).join('\n'),
    }, `${character.name} · 角色图`));
    changePeople({ ...current, characters: [...current.characters, ...additions] });
    setTab('people'); notice(`已确认 ${additions.length} 名角色并创建形象节点；选择工作流后运行生成`);
    if (generate) {
      applyBatchWorkflow(ids, generationConfig);
      if (selectedId) useStudio.setState(state => ({ nodes: state.nodes.map(node => ({ ...node, selected: node.id === selectedId })) }));
      run(ids);
    }
  }

  function adoptCharacterImage(characterId: string, assetId: string) {
    const current = peopleRef.current;
    if (!current.characters.some(character => character.id === characterId)) { notice('关联角色已不存在，图片仅在当前节点采用'); return; }
    changePeople({ ...current, characters: current.characters.map(character => character.id === characterId ? { ...character, assetId } : character) });
    notice('已采用此形象，并更新角色库参考图');
  }

  function importLocations(locations: LocationDraft[], taskId: string, generate = false, generationConfig?: Config) {
    if (generate && runLock.current) return;
    generationConfig = { ...generationConfig, visualStyle: generationConfig?.visualStyle || useStudio.getState().tasks.find(task => task.id === taskId)?.snapshot.config.visualStyle };
    const selectedId = useStudio.getState().nodes.find(node => node.selected)?.id;
    const current = peopleRef.current;
    const existing = new Set(current.locations.map(location => location.sourceKey));
    const additions = locations.map((location, index) => ({ ...location, id: crypto.randomUUID(), sourceKey: `${taskId}:${index}` }))
      .filter(location => !existing.has(location.sourceKey));
    if (!additions.length && !generate) { notice('这次任务的场景已确认，可在场景库中编辑'); return; }
    const baseY = Math.max(0, ...useStudio.getState().nodes.map(node => node.position.y + (node.measured?.height || 350))) + 80;
    const targets = locations.map((_, index) => [...current.locations, ...additions].find(location => location.sourceKey === `${taskId}:${index}`)!);
    const ids = targets.map((location, index) => useStudio.getState().nodes.find(node => node.data.kind === 'image.location' && node.data.config.locationId === location.id)?.id || useStudio.getState().add('image.location', { x: 140 + index % 3 * 330, y: baseY + Math.floor(index / 3) * 400 }, {
      provider: generationConfig?.provider, workflowId: generationConfig?.workflowId, referenceIds: generationConfig?.referenceIds,
      locationId: location.id,
      visualStyle: generationConfig?.visualStyle,
      prompt: [`场景四视图设定：${location.name}`, location.description, location.layout && `布局：${location.layout}`,
        location.restrictions && `限制：${location.restrictions}`, '同一空间前、右、后、左四个方向，2×2 四宫格放在一张图中，不添加人物或文字。'].filter(Boolean).join('\n'),
    }, `${location.name} · 场景图`));
    changePeople({ ...current, locations: [...current.locations, ...additions] });
    setTab('people'); notice(`已确认 ${additions.length} 处场景并创建四视图节点；选择工作流后运行生成`);
    if (generate) {
      applyBatchWorkflow(ids, generationConfig);
      if (selectedId) useStudio.setState(state => ({ nodes: state.nodes.map(node => ({ ...node, selected: node.id === selectedId })) }));
      run(ids);
    }
  }

  function applyBatchWorkflow(ids: string[], config?: Config) {
    if (!config) return;
    const selection: Config = {};
    if (config.provider !== undefined) selection.provider = config.provider;
    if (config.workflowId !== undefined) selection.workflowId = config.workflowId;
    if (config.visualStyle !== undefined) selection.visualStyle = config.visualStyle;
    if (!Object.keys(selection).length) return;
    for (const id of ids) {
      const studio = useStudio.getState();
      const node = studio.nodes.find(item => item.id === id);
      if (node) studio.patch(id, { config: { ...node.data.config, ...selection } });
    }
  }

  function adoptLocationImage(locationId: string, assetId: string) {
    const current = peopleRef.current;
    if (!current.locations.some(location => location.id === locationId)) { notice('关联场景已不存在，图片仅在当前节点采用'); return; }
    changePeople({ ...current, locations: current.locations.map(location => location.id === locationId ? { ...location, assetId } : location) });
    notice('已采用四视图，并更新场景库参考图');
  }

  function importShots(shots: Shot[]) {
    const start = studio.nodes.length;
    shots.forEach((shot, i) => {
      const scene = people.scenes?.find(s => s.id === shot.sceneId), location = people.locations.find(l => l.id === (shot.locationRef?.id || scene?.locationId));
      const refs = shot.characterRefs || people.characters.filter(c => c.assetId || c.referenceIds?.length).map(c => ({ id: c.id, revisionId: c.assetId || c.referenceIds![0] }));
      const locationRef = shot.locationRef || (location?.assetId || location?.referenceIds?.length ? { id: location.id, revisionId: location.assetId || location.referenceIds![0] } : undefined);
      const referenceIds = collectShotReferenceIds({ characterRefs: refs, locationRef, characters: people.characters, locations: people.locations, availableAssetIds: new Set(studio.assets.filter(asset => asset.mime.startsWith('image/')).map(asset => asset.id)) });
      const anchors = people.characters.filter(c => refs.some(r => r.id === c.id)).map(c => [c.name, c.appearance || c.description, c.wardrobe].filter(Boolean).join('：'));
      const image = studio.add('image.generate', { x: 140, y: (start + i) * 280 }, { visualStyle: shot.visualStyle, prompt: [shot.visualPrompt, ...anchors, location?.description, location?.layout, location?.restrictions].filter(Boolean).join('\n'), referenceIds }, shot.title || `分镜 ${i + 1}`);
      const video = useStudio.getState().add('video.image_to_video', { x: 490, y: (start + i) * 280 }, { visualStyle: shot.visualStyle, prompt: shot.cameraMove || '自然流畅的镜头运动', seconds: shot.durationMs / 1000 }, (shot.title || `分镜 ${i + 1}`) + ' · 视频');
      useStudio.getState().connect({ id: crypto.randomUUID(), source: image, target: video, sourceHandle: 'image', targetHandle: 'image', data: { kind: 'data' } });
    });
    changePeople({ ...peopleRef.current, shots: [...peopleRef.current.shots, ...shots.map(s => ({ ...s, id: crypto.randomUUID(), status: 'draft' }))] });
    notice(`已添加 ${shots.length} 组分镜图与视频节点`);
  }

  if (fatal) return <div className="connection-screen"><AlertCircle size={32}/><h1>工作台尚未连接</h1><p>{fatal}</p><p>请在项目目录运行 <code>pnpm dev</code>，使用启动器打开的地址。</p><button onClick={() => location.reload()}>重新连接</button></div>;
  if (!ready) return <div className="connection-screen"><Layers3 size={30}/><h1>正在打开无限画布</h1><p>连接本地项目服务…</p></div>;

  async function renameAsset(asset: Asset, name: string) {
    const scope = captureProject();
    if (!scope.current() || asset.projectId !== scope.id) throw new Error('项目已切换，请重新选择素材');
    const updated = await api<Asset>(`/assets/${asset.id}`, json('PATCH', { name }));
    if (!scope.current()) return;
    useStudio.setState(s => ({ assets: s.assets.map(item => item.id === updated.id ? updated : item) }));
    setPreviewAsset(current => current?.id === updated.id ? updated : current);
    notice('素材名称已保存');
  }
  const settingsScope = captureProject();
  return <div className="app-shell">
    <header className="app-header"><div className="brand"><Layers3 size={23}/><div>无限画布<small>短剧创作工作台</small></div></div><div className="project-switch"><FolderOpen size={15}/><select aria-label="当前项目" disabled={!!runStage} value={project?.id || ''} onChange={e => void act(() => openProject(e.target.value))}><option value="" disabled>选择项目</option>{projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select><ChevronDown size={12}/><button title="新建项目" aria-label="新建项目" disabled={!!runStage} onClick={() => setNewProject(true)}><Plus size={16}/></button></div><span className="save-status" title={saveError || undefined}><span className={'status-dot ' + (saving ? 'running' : saveError ? 'failed' : 'completed')}/>{saving ? '保存中' : saveError ? '保存失败（修改仍保留）' : studio.edits === studio.savedEdits && !timelineDirty.current && !peopleDirty.current ? '已保存到本机' : '有未保存修改'}</span><div className="header-actions"><button disabled={!project} onClick={() => void act(async () => { await save(); notice('项目已保存'); })}><Save size={15}/>{saveError ? '重试保存' : '保存'}</button><button className="primary" disabled={!!runStage || !project || !studio.nodes.length} onClick={() => run(studio.nodes.filter(n => n.selected).map(n => n.id))}><Play size={15}/>{runStage || (studio.nodes.some(n => n.selected) ? '运行选区' : '运行画布')}</button></div></header>
    <div className="project-tools"><details><summary>项目工具</summary><div><button disabled={!project} onClick={() => void act(() => downloadProject())}><Download size={14}/>导出完整项目</button><button onClick={() => projectInput.current?.click()}><Upload size={14}/>导入项目包</button><button disabled={!project} onClick={() => void act(() => downloadProject(true))}>导出画布模板</button><button disabled={!project} onClick={() => templateInput.current?.click()}>导入画布模板</button></div></details><button aria-label="打开工作台设置" onClick={() => { setSettingsTab('services'); setSettingsOpen(true); }}><Settings2 size={14}/>设置</button></div>
    <div className="workspace" inert={!project}>
      {sidebar && <aside className="sidebar"><div className="sidebar-head"><span>创作资源</span><button aria-label="收起侧栏" onClick={() => setSidebar(false)}><PanelLeftClose size={14}/></button></div><div className="sidebar-tabs">{[['nodes', '节点'], ['assets', '素材'], ['people', '角色 / 场景']].map(([id, label]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label}</button>)}</div>
      {tab !== 'people' && <label className="search-box"><Search size={14}/><input aria-label="搜索节点或素材" placeholder={tab === 'nodes' ? '搜索节点' : '搜索素材'} value={search} onChange={e => setSearch(e.target.value)}/></label>}
      <div className="sidebar-content">
        {tab === 'nodes' && <>{Object.entries(studio.definitions).filter(([kind, d]) => !['video.sound_effects', 'audio.tts'].includes(kind) && d.displayName.includes(search)).map(([kind, d]) => <button disabled={!project} className="toolbox-node" key={kind} draggable onDragStart={e => e.dataTransfer.setData('application/canvas-kind', kind)} onClick={() => studio.add(kind)}><span className={'tool-icon ' + kind.split('.')[0]}>{(kind.includes('video') || kind === 'frame.extract') ? <Film size={16}/> : kind.includes('audio') ? <AudioLines size={16}/> : kind.includes('image') ? <Image size={16}/> : kind.startsWith('character') ? <UserRound size={16}/> : kind.startsWith('location') ? <MapPin size={16}/> : <span>文</span>}</span><span>{d.displayName}</span><Plus size={12}/></button>)}<p className="sidebar-tip">点击添加，或拖到画布<br/>从输出端口拉线建立依赖</p></>}
        {tab === 'assets' && <><button className="import-button" disabled={!project} onClick={() => fileInput.current?.click()}><Upload size={15}/>导入图片 / 视频 / 音频</button>{studio.assets.filter(a => a.name.includes(search)).map(a => <div className="asset-item" key={a.id}><button className="asset-preview" onClick={() => setPreviewAsset(a)}>{a.mime.startsWith('image/') ? <img src={thumbnailUrl(a.id)} alt={a.name} loading="lazy"/> : a.mime.startsWith('video/') ? <Film size={24}/> : <AudioLines size={24}/>}</button><div><strong title={a.name}>{a.name}</strong><small>{a.mime.split('/')[0]} · {a.sha256.slice(0, 6)}</small><div className="asset-actions"><AssetRename name={a.name} rename={name => renameAsset(a, name)}/><button onClick={() => { studio.add('asset.' + a.mime.split('/')[0], undefined, { assetId: a.id }, a.name); }}>加入画布</button><button aria-label={`移除${a.name}`} onClick={() => void act(async () => { if (!confirm('移除素材后，引用此版本的节点与导出将提示缺失。继续？')) return; await api(`/assets/${a.id}`, { method: 'DELETE' }); useStudio.setState(s => ({ assets: s.assets.filter(x => x.id !== a.id) })); })}><Trash2 size={12}/></button></div></div></div>)}{!studio.assets.length && <p className="sidebar-tip">导入参考图开始创作。<br/>云端生成的候选也会保存在这里。</p>}</>}
        {tab === 'people' && <>{(['episodes', 'scenes'] as const).map(type => <section className="profile-section" key={type}><h3>{type === 'episodes' ? '剧集' : '剧情场景'}<button aria-label={type === 'episodes' ? '添加剧集' : '添加剧情场景'} disabled={!project} onClick={() => setRecordEdit({ type, record: { id: crypto.randomUUID(), name: '', script: '' } })}><Plus size={14}/></button></h3>{(people[type] || []).map(record => <article className="entity-row" key={record.id}><strong>{record.name}</strong><button onClick={() => setRecordEdit({ type, record })}>编辑</button></article>)}</section>)}{(['characters', 'locations'] as const).map(type => <section className="profile-section" key={type}><h3>{type === 'characters' ? '角色' : '场景'}<button aria-label={type === 'characters' ? '添加角色' : '添加场景'} disabled={!project} onClick={() => setProfileEdit({ type, profile: { id: crypto.randomUUID(), name: '', description: '' } })}><Plus size={14}/></button></h3>{people[type].map(profile => <article className="profile-card" key={profile.id}><strong>{profile.name}</strong><p>{profile.description || '尚未填写描述'}</p>{profile.wardrobe && <small>服装：{profile.wardrobe}</small>}<button onClick={() => setProfileEdit({ type, profile })}>编辑</button><button onClick={() => studio.add(type === 'characters' ? 'character.reference' : 'location.reference', undefined, { assetId: profile.assetId, prompt: [profile.description, profile.appearance, profile.wardrobe, profile.layout, profile.restrictions].filter(Boolean).join('\n') }, profile.name)}>加入画布</button></article>)}{!people[type].length && <p className="muted">添加{type === 'characters' ? '角色外貌与参考图' : '地点描述与参考图'}</p>}</section>)}<section className="profile-section"><h3>分镜草案 <span>{people.shots.length}</span></h3>{people.shots.map((shot, i) => <p key={shot.id || i}>{i + 1}. {shot.title || shot.visualPrompt.slice(0, 24)}</p>)}<small>运行「提取分镜」后，人工确认草案即可创建镜头节点。</small></section></>}
      </div><div className="provider-status"><label className="check-row"><input type="checkbox" disabled={!project} checked={project?.settings.cloudEnabled || false} onChange={e => void act(async () => { const scope = captureProject(); if (!scope.current()) return; const p = await api<Project>(`/projects/${scope.id}/settings`, json('PUT', { cloudEnabled: e.target.checked })); if (scope.current()) setProject(p); })}/>{project?.settings.cloudEnabled ? <Cloud size={14}/> : <HardDrive size={14}/>} {project?.settings.cloudEnabled ? '允许云端生成' : '仅本地编辑'}</label>{providers.map(p => <div key={p.id}><span className={'status-dot ' + (p.ready ? 'completed' : 'idle')}/>{p.name}<small>{p.ready ? '已配置' : '未配置'}</small></div>)}</div></aside>}
      <main className="main-workspace"><div className="canvas-toolbar"><div>{!sidebar && <button aria-label="展开资源栏" onClick={() => setSidebar(true)}><Layers3 size={15}/></button>}<span className="eyebrow">创作画布</span><span className="muted">{studio.nodes.length} 节点 · {studio.edges.length} 连线</span></div><div><button title="撤销 Ctrl+Z" aria-label="撤销" disabled={!studio.past.length} onClick={studio.undo}><Undo2 size={15}/></button><button title="重做 Ctrl+Shift+Z" aria-label="重做" disabled={!studio.future.length} onClick={studio.redo}><Redo2 size={15}/></button><i/><button title="复制 Ctrl+D" aria-label="复制选中节点" onClick={studio.duplicate}><Copy size={15}/></button><button title="删除 Delete" aria-label="删除选中对象" onClick={studio.remove}><Trash2 size={15}/></button></div></div><div className="canvas-and-inspector"><ReactFlowProvider key={project?.id || 'empty'}><Canvas notice={notice} hidePreviews={canvasPreferences.canvasHidePreviews} previewThreshold={canvasPreferences.canvasPreviewThreshold}/></ReactFlowProvider><Inspector {...{ generationOptions, runStage, people }} run={run} addClip={addClip} importShots={importShots} importCharacters={importCharacters} adoptCharacterImage={adoptCharacterImage} importLocations={importLocations} adoptLocationImage={adoptLocationImage}/></div><Timeline taskActivitySignal={taskActivitySignal} timeline={timeline} change={changeTimeline} cancel={id => void act(async () => { await api(`/tasks/${id}/cancel`, json('POST', {})); notice('已请求取消；云端任务可能继续运行，迟到结果不会自动采用'); })} retry={(id, uncertain) => void act(async () => { if (uncertain && !confirm('请先在 RunningHub 核查该次提交。再次提交可能重复计费，确认重新提交？')) return; await api(`/tasks/${id}/retry`, json('POST', { confirmUncertain: uncertain })); })} exportJob={exportJob} exportVideo={() => void act(async () => { const scope = captureProject(); if (!scope.current()) return; await save(); if (!scope.current()) return; const job = await api<ExportJob>('/exports', json('POST', { projectId: scope.id })); if (scope.current()) setExportJob(job); })}/></main>
    </div>
    <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp,video/mp4,video/webm,video/quicktime,audio/*" multiple hidden onChange={e => { const files = Array.from(e.target.files || []); e.target.value = ''; void act(async () => { const scope = captureProject(); for (const file of files) { if (!scope.current()) return; const body = new FormData(); body.set('projectId', scope.id); body.set('file', file); const a = await api<Asset>('/assets/import', { method: 'POST', body }); if (!scope.current()) return; useStudio.setState(s => ({ assets: [a, ...s.assets] })); } notice(`已导入 ${files.length} 个素材`); }); }}/>
    <input ref={projectInput} type="file" accept="application/zip,.zip" hidden onChange={e => { const file = e.target.files?.[0]; e.target.value = ''; if (file) void act(async () => { const body = new FormData(); body.set('file', file); const p = await api<Project>('/projects/import', { method: 'POST', body }); setProjects(ps => [p, ...ps]); await openProject(p.id); notice('项目包已校验并导入为新项目，云端生成保持关闭'); }); }}/>
    <input ref={templateInput} type="file" accept="application/json,.json" hidden onChange={e => { const file = e.target.files?.[0]; e.target.value = ''; if (file) void act(async () => { const scope = captureProject(); if (!scope.current()) return; await save(); const content = JSON.parse(await file.text()); if (!scope.current()) return; const canvas = await api<CanvasDoc>(`/projects/${scope.id}/template`, json('POST', content)); if (!scope.current()) return; useStudio.getState().load(canvas); notice('模板已加入画布，请重新绑定参考素材'); }); }}/>
    {settingsOpen && <Settings initialTab={settingsTab} project={project} changeProject={updated => { if (settingsScope.current() && updated.id === settingsScope.id) setProject(updated); }} saved={refreshProviders} close={() => setSettingsOpen(false)}/>}
    {recordEdit && <div className="modal-backdrop"><form className="dialog record-dialog" onSubmit={e => { e.preventDefault(); const { type, record } = recordEdit; const values = peopleRef.current[type] || []; changePeople({ ...peopleRef.current, [type]: values.some(v => v.id === record.id) ? values.map(v => v.id === record.id ? record : v) : [...values, record] }); setRecordEdit(undefined); }}><header><h2>{recordEdit.type === 'episodes' ? '剧集' : '剧情场景'}</h2><button type="button" aria-label="关闭剧情编辑" onClick={() => setRecordEdit(undefined)}><X size={18}/></button></header><label>名称<input required value={recordEdit.record.name} onChange={e => setRecordEdit({ ...recordEdit, record: { ...recordEdit.record, name: e.target.value } })}/></label>{recordEdit.type === 'scenes' && <><label>所属剧集<select value={recordEdit.record.episodeId || ''} onChange={e => setRecordEdit({ ...recordEdit, record: { ...recordEdit.record, episodeId: e.target.value || undefined } })}><option value="">独立场景</option>{people.episodes?.map(episode => <option key={episode.id} value={episode.id}>{episode.name}</option>)}</select></label><label>场景设定<select value={recordEdit.record.locationId || ''} onChange={e => setRecordEdit({ ...recordEdit, record: { ...recordEdit.record, locationId: e.target.value || undefined } })}><option value="">暂不关联</option>{people.locations.map(location => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label></>}<label>剧本<textarea rows={8} value={recordEdit.record.script} onChange={e => setRecordEdit({ ...recordEdit, record: { ...recordEdit.record, script: e.target.value } })}/></label><div className="field-row"><button type="button" disabled={!recordEdit.record.script.trim()} onClick={() => studio.add('story.prompt', undefined, { prompt: recordEdit.record.script }, recordEdit.record.name || '剧本')}>加入故事节点</button><button type="submit" className="primary">保存剧情</button></div></form></div>}
    {message && <div className="toast" role="status"><span>{message}</span><button aria-label="关闭提示" onClick={() => notice('')}><X size={15}/></button></div>}
    {newProject && !settingsOpen && <div className="modal-backdrop"><form className="dialog" onSubmit={e => { e.preventDefault(); void act(createProject); }}><header><h2>新建短剧项目</h2>{project && <button type="button" onClick={() => setNewProject(false)}><X size={18}/></button>}</header><p>画布、参考素材和镜头版本将保存在本机。</p><button type="button" onClick={() => { setSettingsTab('storage'); setSettingsOpen(true); }}>设置数据保存路径</button><label>项目名称<input autoFocus required maxLength={100} placeholder="例如：雨夜来信" value={name} onChange={e => setName(e.target.value)}/></label><button type="submit" className="primary" disabled={!name.trim()}><Plus size={15}/>创建项目</button></form></div>}
    {profileEdit && <div className="modal-backdrop"><form className="dialog profile-dialog" onSubmit={e => { e.preventDefault(); const { type, profile } = profileEdit; if (profile.voiceAssetId && !profile.voiceAuthorized) { notice('请确认参考声音的使用授权'); return; } const list = peopleRef.current[type]; changePeople({ ...peopleRef.current, [type]: list.some(p => p.id === profile.id) ? list.map(p => p.id === profile.id ? profile : p) : [...list, profile] }); setProfileEdit(undefined); }}><header><h2>{profileEdit.type === 'characters' ? '角色设定' : '场景设定'}</h2><button type="button" aria-label="关闭设定" onClick={() => setProfileEdit(undefined)}><X size={18}/></button></header><label>名称<input required value={profileEdit.profile.name} onChange={e => editProfile({ name: e.target.value })}/></label><label>描述<textarea rows={3} value={profileEdit.profile.description} onChange={e => editProfile({ description: e.target.value })}/></label>{profileEdit.type === 'characters' && <><div className="field-row"><label>外貌锚点<input value={profileEdit.profile.appearance || ''} onChange={e => editProfile({ appearance: e.target.value })}/></label><label>服装版本<input value={profileEdit.profile.wardrobe || ''} onChange={e => editProfile({ wardrobe: e.target.value })}/></label></div><label>音色描述<input value={profileEdit.profile.voice || ''} onChange={e => editProfile({ voice: e.target.value })}/></label><label>授权参考声音<select value={profileEdit.profile.voiceAssetId || ''} onChange={e => editProfile({ voiceAssetId: e.target.value || undefined })}><option value="">使用模型音色</option>{studio.assets.filter(a => a.mime.startsWith('audio/')).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>{profileEdit.profile.voiceAssetId && <label className="check-row"><input type="checkbox" checked={profileEdit.profile.voiceAuthorized || false} onChange={e => editProfile({ voiceAuthorized: e.target.checked })}/>我已获得参考声音的使用授权</label>}</>}{profileEdit.type === 'locations' && <label>空间布局<textarea rows={3} value={profileEdit.profile.layout || ''} onChange={e => editProfile({ layout: e.target.value })}/></label>}<label>参考图版本<select aria-label="参考图版本" value={profileEdit.profile.assetId || ''} onChange={e => editProfile({ assetId: e.target.value || undefined })}><option value="">暂不绑定</option>{studio.assets.filter(a => a.mime.startsWith('image/')).map(a => <option key={a.id} value={a.id}>{a.name} · {a.sha256.slice(0, 6)}</option>)}</select></label><details><summary>更多参考图与限制</summary><div className="reference-list">{studio.assets.filter(a => a.mime.startsWith('image/')).map(a => <label className="check-row" key={a.id}><input type="checkbox" checked={profileEdit.profile.referenceIds?.includes(a.id) || false} onChange={e => editProfile({ referenceIds: e.target.checked ? [...(profileEdit.profile.referenceIds || []), a.id] : profileEdit.profile.referenceIds?.filter(id => id !== a.id) })}/>{a.name} · {a.sha256.slice(0, 6)}</label>)}</div><label>限制项<textarea rows={2} value={profileEdit.profile.restrictions || ''} onChange={e => editProfile({ restrictions: e.target.value })}/></label></details><button className="primary" type="submit">保存设定</button></form></div>}
    {previewAsset && <div className="modal-backdrop" onClick={() => setPreviewAsset(undefined)}><div className="preview-dialog" onClick={e => e.stopPropagation()}><header><strong>{previewAsset.name}</strong><button onClick={() => setPreviewAsset(undefined)}>关闭</button></header>{previewAsset.mime.startsWith('image/') ? <img src={mediaUrl(previewAsset.id)} alt={previewAsset.name}/> : previewAsset.mime.startsWith('video/') ? <video src={mediaUrl(previewAsset.id)} controls/> : <audio src={mediaUrl(previewAsset.id)} controls/>}<a href={downloadUrl(previewAsset.id)} download={previewAsset.name}>下载素材</a></div></div>}
  </div>;
}
