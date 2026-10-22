/* Decorative topographic contour background (marching squares over animated noise).
   Purely presentational: nothing else depends on it. */
export function startTopographicBackground(canvas) {
const SN=(function(){
 const F3=1/3,G3=1/6,g=[[1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],[1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],[0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]];
 function S(seed){this.perm=new Uint8Array(512);this.pm=new Uint8Array(512);const p=new Uint8Array(256);for(let i=0;i<256;i++)p[i]=i;
  for(let i=255;i>0;i--){seed=(seed*16807)%2147483647;const j=seed%(i+1),t=p[i];p[i]=p[j];p[j]=t}
  for(let i=0;i<512;i++){this.perm[i]=p[i&255];this.pm[i]=this.perm[i]%12}}
 S.prototype.n=function(xin,yin,zin){const P=this.perm,M=this.pm;let n0,n1,n2,n3;
  const s=(xin+yin+zin)*F3,i=Math.floor(xin+s),j=Math.floor(yin+s),k=Math.floor(zin+s),t=(i+j+k)*G3;
  const x0=xin-(i-t),y0=yin-(j-t),z0=zin-(k-t);let i1,j1,k1,i2,j2,k2;
  if(x0>=y0){if(y0>=z0){i1=1;j1=0;k1=0;i2=1;j2=1;k2=0}else if(x0>=z0){i1=1;j1=0;k1=0;i2=1;j2=0;k2=1}else{i1=0;j1=0;k1=1;i2=1;j2=0;k2=1}}
  else{if(y0<z0){i1=0;j1=0;k1=1;i2=0;j2=1;k2=1}else if(x0<z0){i1=0;j1=1;k1=0;i2=0;j2=1;k2=1}else{i1=0;j1=1;k1=0;i2=1;j2=1;k2=0}}
  const x1=x0-i1+G3,y1=y0-j1+G3,z1=z0-k1+G3,x2=x0-i2+2*G3,y2=y0-j2+2*G3,z2=z0-k2+2*G3,x3=x0-1+3*G3,y3=y0-1+3*G3,z3=z0-1+3*G3;
  const ii=i&255,jj=j&255,kk=k&255;
  const c=(tt,gi,x,y,z)=>{if(tt<0)return 0;tt*=tt;return tt*tt*(g[gi][0]*x+g[gi][1]*y+g[gi][2]*z)};
  n0=c(0.6-x0*x0-y0*y0-z0*z0,M[ii+P[jj+P[kk]]],x0,y0,z0);
  n1=c(0.6-x1*x1-y1*y1-z1*z1,M[ii+i1+P[jj+j1+P[kk+k1]]],x1,y1,z1);
  n2=c(0.6-x2*x2-y2*y2-z2*z2,M[ii+i2+P[jj+j2+P[kk+k2]]],x2,y2,z2);
  n3=c(0.6-x3*x3-y3*y3-z3*z3,M[ii+1+P[jj+1+P[kk+1]]],x3,y3,z3);
  return 32*(n0+n1+n2+n3)};
 return S})();
const noise=new SN(73),cv=canvas,ctx=cv.getContext('2d');
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches,dpr=Math.min(window.devicePixelRatio||1,1.5);
const NUM=11,SCALE=0.003;
let W,H,CELL,cols,rows,field,time=0;
const isDark=()=>{const t=document.documentElement.dataset.theme;return t==='dark'||(t!=='light'&&matchMedia('(prefers-color-scheme:dark)').matches)};
const PAL={dark:{lo:[139,92,246],mid:[167,139,250],hi:[217,70,239],k:.7},light:{lo:[109,63,209],mid:[139,92,246],hi:[168,85,247],k:.5}};
const mix=(a,b,t)=>a.map((v,i)=>Math.round(v+(b[i]-v)*t));
function fbm(x,y,z){let v=0,a=1,f=1,s=0;for(let o=0;o<4;o++){v+=noise.n(x*f,y*f,z)*a;s+=a;a*=.5;f*=2}return v/s}
const ET=[[],[[3,2]],[[2,1]],[[3,1]],[[1,0]],[[1,0],[3,2]],[[2,0]],[[3,0]],[[0,3]],[[0,2]],[[0,3],[2,1]],[[0,1]],[[1,3]],[[1,2]],[[2,3]],[]];
const lerp=(a,b,t)=>Math.abs(b-a)<1e-4?.5:(t-a)/(b-a);
let px=0,py=0;
function pt(e,cx,cy,tl,tr,br,bl,th){
 if(e===0){px=cx+lerp(tl,tr,th)*CELL;py=cy}
 else if(e===1){px=cx+CELL;py=cy+lerp(tr,br,th)*CELL}
 else if(e===2){px=cx+lerp(bl,br,th)*CELL;py=cy+CELL}
 else{px=cx;py=cy+lerp(tl,bl,th)*CELL}}
function resize(){
 W=window.innerWidth;H=window.innerHeight;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
 CELL=W<700?18:12;cols=Math.ceil(W/CELL)+1;rows=Math.ceil(H/CELL)+1;field=new Float32Array(cols*rows);
 frame()}
function frame(){
 ctx.clearRect(0,0,W,H);
 for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){
  const x=i*CELL,y=j*CELL;let v=fbm(x*SCALE,y*SCALE,time);
  field[j*cols+i]=v}
 let mn=Infinity,mxv=-Infinity;
 for(let k=0;k<field.length;k++){if(field[k]<mn)mn=field[k];if(field[k]>mxv)mxv=field[k]}
 const rg=mxv-mn||1;for(let k=0;k<field.length;k++)field[k]=(field[k]-mn)/rg;
 const pal=PAL[isDark()?'dark':'light'];
 ctx.lineCap='round';
 for(let c=0;c<NUM;c++){
  const th=(c+1)/(NUM+1),col=th<.5?mix(pal.lo,pal.mid,th*2):mix(pal.mid,pal.hi,(th-.5)*2);
  const base=(.25+(1-Math.abs(th-.5)*2)*.45)*pal.k,major=c%5===0;
  ctx.beginPath();
  for(let j=0;j<rows-1;j++)for(let i=0;i<cols-1;i++){
   const tl=field[j*cols+i],tr=field[j*cols+i+1],br=field[(j+1)*cols+i+1],bl=field[(j+1)*cols+i];
   const ci=(tl>=th?8:0)|(tr>=th?4:0)|(br>=th?2:0)|(bl>=th?1:0),ed=ET[ci];
   if(!ed.length)continue;
   const cx=i*CELL,cy=j*CELL;
   for(let e=0;e<ed.length;e++){pt(ed[e][0],cx,cy,tl,tr,br,bl,th);ctx.moveTo(px,py);pt(ed[e][1],cx,cy,tl,tr,br,bl,th);ctx.lineTo(px,py)}}
  const rgb=col.join(',');
  if(major){ctx.strokeStyle='rgba('+rgb+','+(base*.25)+')';ctx.lineWidth=4.5;ctx.stroke()}
  ctx.strokeStyle='rgba('+rgb+','+(base*(major?1:.8))+')';ctx.lineWidth=major?1.2:.7;ctx.stroke()}}
window.addEventListener('resize',resize);
resize();
matchMedia('(prefers-color-scheme:dark)').addEventListener('change',frame);
if(!reduce){let last=0;const loop=ts=>{if(!last)last=ts;const d=ts-last;if(d>=33){time+=d/1000*.15;last=ts;frame()}requestAnimationFrame(loop)};requestAnimationFrame(loop)}
}
