'use strict';
const $=id=>document.getElementById(id);
let maps=[];
function selectMap(id){
 const m=maps.find(x=>x.id===id)||maps[0];
 document.querySelectorAll('.map-card').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.map===m.id)));
 $('selected-kicker').textContent=`GATHERING STORM / ${m.size.toUpperCase()} / ${m.width} × ${m.height}`;
 $('selected-title').textContent=`${m.region} · ${m.epoch}`;
 $('selected-description').textContent=m.description;
 $('selected-stats').textContent=`${m.stats.tiles.toLocaleString()} hexes · ${m.stats.land.toLocaleString()} land · ${m.stats.resource_tiles.toLocaleString()} resource tiles`;
 $('native-download').href=m.native_url;$('native-download').download=m.file;
 $('package-download').href=m.package_url;
 $('full-inspector').href=m.inspector_url;
 $('map-readme').href=m.readme_url;$('map-sources').href=m.sources_url;
 $('resource-audit').hidden=!m.id.startsWith('hawaii');$('resource-audit').href='maps/hawaii/RESOURCE_AUDIT.md';
 $('map-note').textContent=m.id.startsWith('hawaii')?'All islands connect through Coast water for early ships. Both climates include modern crops and introduced animals. Six suggested maritime starts; island sizes are asymmetric.':m.id.endsWith('lgm')?'Approximate ~21 ka reconstruction: sea level −125 m, expanded natural lakes, and alpine ice represented by impassable Snow Mountain.':'California and its neighbors, with authored river networks, iconic resource districts, traversable valley floors, and suggested civilization starts.';
 const target=m.inspector_url+(m.query?'&':'?')+'embedded=1';
 if($('inspector').getAttribute('src')!==target)$('inspector').src=target;
 $('inspector').title=`Interactive ${m.region} ${m.epoch} map inspector`;
 document.title=`${m.region} · ${m.epoch} | Regional Atlas`;
 const q=new URLSearchParams(location.search);q.set('map',m.id);history.replaceState(null,'',location.pathname+'?'+q.toString()+location.hash);
}
async function init(){
 try{
  const response=await fetch('maps.json');if(!response.ok)throw Error('Map collection could not be loaded.');maps=await response.json();
  $('collection').replaceChildren(...maps.map(m=>{const button=document.createElement('button');button.type='button';button.className='map-card';button.dataset.map=m.id;button.setAttribute('aria-pressed','false');button.setAttribute('aria-label',`${m.region}, ${m.epoch}, ${m.size}, ${m.width} by ${m.height}`);
   const preview=document.createElement('div');preview.className='card-preview';const img=document.createElement('img');img.src=m.preview_url;img.alt='';img.width=300;img.height=150;const era=document.createElement('span');era.className='era';era.textContent=m.epoch==='Modern'?'Modern':'Ice Age · ~21 ka';preview.append(img,era);
   const copy=document.createElement('div');copy.className='card-copy';const title=document.createElement('strong');title.textContent=m.region;const detail=document.createElement('small');detail.textContent=`${m.size} · ${m.width} × ${m.height}`;copy.append(title,detail);button.append(preview,copy);button.addEventListener('click',()=>selectMap(m.id));return button;}));
  selectMap(new URLSearchParams(location.search).get('map'));
 }catch(error){$('collection').replaceChildren();const p=document.createElement('p');p.className='error';p.textContent=error.message+' Direct downloads remain available above.';$('collection').append(p);}
}
init();
