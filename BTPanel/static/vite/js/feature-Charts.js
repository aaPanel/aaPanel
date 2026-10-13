;(() => {
	const stylesheetSelector = "link[rel=stylesheet]"
	const loaded = new Set(Array.from(document.querySelectorAll(stylesheetSelector)).map(link => link.href))
	const version = "1791538283700"
	const findLoadedLink = href => Array.from(document.querySelectorAll(stylesheetSelector)).find(link => link.href === href)
	const removeAfterLoad = (freshLink, staleLink) => {
		const remove = () => staleLink.remove()
		if (freshLink.sheet) {
			requestAnimationFrame(remove)
			return
		}
		freshLink.addEventListener("load", remove, { once: true })
	}
	for (const link of Array.from(document.querySelectorAll(stylesheetSelector))) {
		const url = new URL(link.href, location.href)
		if (url.origin !== location.origin || url.searchParams.get("v") === version) continue
		url.searchParams.set("v", version)
		if (loaded.has(url.href)) {
			const freshLink = findLoadedLink(url.href)
			if (freshLink && freshLink !== link) removeAfterLoad(freshLink, link)
			continue
		}
		const freshLink = document.createElement("link")
		freshLink.rel = "stylesheet"
		freshLink.href = url.href
		link.parentNode?.insertBefore(freshLink, link.nextSibling)
		loaded.add(url.href)
		removeAfterLoad(freshLink, link)
	}
})();
import{r as e}from"./rolldown-runtime.js?v=1791538283700";import{An as t,Bn as n,Kn as r,Qr as i,Un as a,Yn as o,b as s,f as c,kr as l,n as u,rn as d,sr as f,wn as p,xr as m}from"./vendor-utils.js?v=1791538283700";import{an as h}from"./vendor-naive.js?v=1791538283700";import{zf as g}from"./app.js?v=1791538283700";import{A as _,D as v,E as y,N as b,O as x,S,_ as C,a as w,c as T,d as E,f as D,h as O,i as k,k as A,l as j,m as M,o as N,p as P,s as F,u as I}from"./vendor-charts.js?v=1791538283700";d(),b([P,C,j,O,N,F,I,v,_,w,k]);var L=A,R=t({__name:`index`,props:{width:{type:[Number,String],default:`100%`},height:{type:[Number,String],default:`200px`},dataZoom:{type:Boolean,default:!1},option:{type:Object,required:!0}},setup(e,{expose:t}){let c=e,u=m(null),d=null;function g(){u.value!==null&&(d=L.getInstanceByDom(u.value),d==null&&(d=L.init(u.value)),d.setOption(c.option,!0))}function _(){var e;u.value!==null&&((e=L.getInstanceByDom(u.value))==null||e.resize())}f(()=>c.option,e=>{e&&n(()=>{g()})},{immediate:!0,deep:!0});let v=s(_,300,{maxWait:800});return r(()=>{g(),window.addEventListener(`resize`,v)}),a(()=>{var e;u.value&&((e=L.getInstanceByDom(u.value))==null||e.dispose(),window.removeEventListener(`resize`,v))}),t({getChart:()=>d}),(t,n)=>(o(),p(`div`,{ref_key:`chartRef`,ref:u,style:i({width:l(h)(e.width),height:l(h)(e.height)})},null,4))}}),z=e({default:()=>B}),B=R;b([P,C,j,O,N,F,I,M,x,_,w,k]);var V=A;d();var H=t({__name:`index`,props:{width:{type:[Number,String],default:`100%`},height:{type:[Number,String],default:`200px`},dataZoom:{type:Boolean,default:!1},option:{type:Object,required:!0}},setup(e,{expose:t}){let u=e,d=m(null);function g(){if(d.value===null)return;let e=V.getInstanceByDom(d.value);e==null&&(e=V.init(d.value)),e.setOption(u.option,!0),requestAnimationFrame(()=>e.resize())}function _(){var e;d.value!==null&&((e=V.getInstanceByDom(d.value))==null||e.resize())}f(()=>u.option,e=>{e&&n(()=>{g()})},{immediate:!0,deep:!0});let v=s(_,80,{maxWait:240});return c(d,()=>{v()}),r(()=>{n(()=>{g(),window.addEventListener(`resize`,v)})}),a(()=>{var e;d.value&&((e=V.getInstanceByDom(d.value))==null||e.dispose(),window.removeEventListener(`resize`,v))}),t({resize:_,getChart:()=>V.getInstanceByDom(d.value)}),(t,n)=>(o(),p(`div`,{ref_key:`chartRef`,ref:d,class:`bt-line-chart`,style:i({width:l(h)(e.width),height:l(h)(e.height)})},null,4))}}),U=e({default:()=>W}),W=g(H,[[`__scopeId`,`data-v-ba6e3b19`]]);b([D,P,C,j,O,N,F,I,T,S,_,w,k,E]);var G=A;d();var K=t({__name:`index`,props:{width:{type:[Number,String],default:`100%`},height:{type:[Number,String],default:`200px`},dataZoom:{type:Boolean,default:!1},option:{type:Object,required:!0}},setup(e,{expose:t}){let d=e,g=m(null),_=!0;async function v(){if(_){let{data:e}=await u.get(`/static/vite/data/world.json`);G.registerMap(`world`,e),_=!1}if(g.value===null)return;let e=G.getInstanceByDom(g.value);e==null&&(e=G.init(g.value)),e.setOption(d.option,!0),requestAnimationFrame(()=>e.resize())}function y(){var e;g.value!==null&&((e=G.getInstanceByDom(g.value))==null||e.resize())}f(()=>d.option,e=>{e&&n(()=>{v()})},{immediate:!0,deep:!0});let b=s(y,80,{maxWait:240});return c(g,()=>{b()}),r(async()=>{window.addEventListener(`resize`,b)}),a(()=>{var e;g.value&&((e=G.getInstanceByDom(g.value))==null||e.dispose(),window.removeEventListener(`resize`,b))}),t({resize:y}),(t,n)=>(o(),p(`div`,{ref_key:`chartRef`,ref:g,class:`bt-map-chart`,style:i({width:l(h)(e.width),height:l(h)(e.height)})},null,4))}}),q=e({default:()=>J}),J=g(K,[[`__scopeId`,`data-v-4b805b22`]]);b([D,P,C,j,O,N,F,I,y,_,w,k]);var Y=A;d();var X=t({__name:`index`,props:{width:{type:[Number,String],default:`100%`},height:{type:[Number,String],default:`200px`},dataZoom:{type:Boolean,default:!1},option:{type:Object,required:!0}},setup(e){let t=e,c=m(null);function u(){if(c.value===null)return;let e=Y.getInstanceByDom(c.value);e==null&&(e=Y.init(c.value)),e.setOption(t.option,!0)}function d(){var e;c.value!==null&&((e=Y.getInstanceByDom(c.value))==null||e.resize())}f(()=>t.option,e=>{e&&n(()=>{u()})},{immediate:!0,deep:!0});let g=s(d,300,{maxWait:800});return r(()=>{n(()=>{u(),window.addEventListener(`resize`,g)})}),a(()=>{var e;c.value&&((e=Y.getInstanceByDom(c.value))==null||e.dispose(),window.removeEventListener(`resize`,g))}),(t,n)=>(o(),p(`div`,{ref_key:`chartRef`,ref:c,style:i({width:l(h)(e.width),height:l(h)(e.height)})},null,4))}}),Z=e({default:()=>Q}),Q=X;export{z as a,U as i,q as n,G as r,Z as t};