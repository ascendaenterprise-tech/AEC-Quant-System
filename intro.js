/* Opening intro: diamond layers drop into place, then the curtain sweeps away.
   Plays on every visit. Skip button, click or any key skips it. All motion uses transform/opacity only (GPU compositor), no filters or layout animation.
   Configure with data-* on the script tag. */
(function(){
  var s=document.currentScript||{getAttribute:function(){return null}};
  function a(k,d){return (s.getAttribute&&s.getAttribute('data-'+k))||d}
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce||/[?&]nointro/.test(location.search)||location.hash) return;
  var bg=a('bg','#100826'),bg2=a('bg2','#2a1666'),fg=a('fg','#f4f2fb'),ac=a('accent','#ffd60a'),mut=a('mut','#b9b2d6');
  var sides=[93,72,52,33,13],css='#aecI{position:fixed;inset:0;z-index:2147483000;overflow:hidden;background:radial-gradient(ellipse at 50% 42%,'+bg2+','+bg+' 68%);color:'+fg+';cursor:pointer;transition:transform .9s cubic-bezier(.7,0,.2,1);will-change:transform;transform:translate3d(0,0,0)}'
  +'#aecI.go{transform:translate3d(108%,0,0)}'
  +'#aecI .rule{position:absolute;left:50%;top:0;width:1px;height:100%;background:linear-gradient('+ac+',transparent);transform:scaleY(0);transform-origin:top;animation:aiR .8s cubic-bezier(.3,.7,.2,1) forwards;will-change:transform}'
  +'@keyframes aiR{to{transform:scaleY(1)}}'
  +'#aecI .stage{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.15rem}'
  +'#aecI .dm{position:relative;width:min(32vw,160px);min-width:104px;aspect-ratio:1}'
  +'#aecI .dm i{position:absolute;left:50%;top:50%;border:3px solid '+ac+';opacity:0;animation:aiD .7s cubic-bezier(.22,.9,.24,1.1) forwards;will-change:transform,opacity}'
  +'@keyframes aiD{0%{opacity:0;transform:translate3d(0,-120px,0) scale(1.5) rotate(21deg)}60%{opacity:1}100%{opacity:1;transform:translate3d(0,0,0) scale(1) rotate(45deg)}}'
  +'#aecI .w{font:700 clamp(.8rem,2.1vw,1.1rem)/1 "Chakra Petch","Helvetica Neue",Arial,sans-serif;letter-spacing:.44em;text-transform:uppercase;padding-left:.44em;opacity:0;transform:translate3d(0,12px,0);animation:aiU .6s .9s forwards;text-align:center}'
  +'#aecI .u{font:400 clamp(.6rem,1.5vw,.76rem)/1.6 ui-monospace,Menlo,monospace;letter-spacing:.2em;text-transform:uppercase;color:'+mut+';opacity:0;animation:aiU .6s 1.15s forwards;text-align:center;padding:0 16px}'
  +'@keyframes aiU{to{opacity:1;transform:translate3d(0,0,0)}}'
  +'#aecI .k{position:absolute;right:max(16px,env(safe-area-inset-right,0px));bottom:max(16px,env(safe-area-inset-bottom,0px));background:none;border:1px solid '+mut+';color:'+fg+';font:11px ui-monospace,Menlo,monospace;letter-spacing:.16em;text-transform:uppercase;padding:8px 12px;cursor:pointer;opacity:0;animation:aiU .3s .2s forwards}';
  var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
  var el=document.createElement('div');el.id='aecI';el.setAttribute('role','presentation');el.setAttribute('aria-hidden','true');
  var dm='<div class="dm">';
  for(var i=0;i<sides.length;i++){var n=sides[i];dm+='<i style="width:'+(n/1.6)+'%;height:'+(n/1.6)+'%;margin:-'+(n/3.2)+'% 0 0 -'+(n/3.2)+'%;animation-delay:'+(i*.12)+'s"></i>';}
  dm+='</div>';
  el.innerHTML='<div class="rule"></div><div class="stage">'+dm+'<div class="w"></div><div class="u"></div></div><button class="k" type="button">Skip</button>';
  el.querySelector('.w').textContent=a('word','Ascenda');
  el.querySelector('.u').textContent=a('sub','');
  (document.body||document.documentElement).appendChild(el);
  var de=document.documentElement,prev=de.style.overflow;de.style.overflow='hidden';var done=false;
  function open(){if(done)return;done=true;el.classList.add('go');setTimeout(function(){de.style.overflow=prev;el.remove()},1000)}
  setTimeout(open,2300);el.addEventListener('click',open);document.addEventListener('keydown',open,{once:true});
})();
