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
import{r as e}from"./rolldown-runtime.js?v=1791538283700";import{An as t,Cn as n,Dn as r,It as i,On as a,Sn as o,Yn as s,bn as c,kn as l,kr as u,lr as d,rn as f,ti as p,wn as m,xn as h,xr as g,yr as _}from"./vendor-utils.js?v=1791538283700";import{l as v}from"./vendor-vue.js?v=1791538283700";import{A as y,Ct as b,Et as x,F as S,St as C,T as w,xt as T}from"./vendor-naive.js?v=1791538283700";import{Pf as E,cp as D,ln as O,mn as k}from"./app.js?v=1791538283700";import{Qi as A}from"./app-components.js?v=1791538283700";import{Df as j,Ef as M}from"./app-shared.js?v=1791538283700";import{n as N,r as P}from"./vendor-pdf.js?v=1791538283700";f(),P();var F={class:`leading-20px`},I=t({__name:`index`,props:{type:{default:`site`},data:{},callback:{}},setup(e){let{t}=v(),n=e,f=c(()=>{let{data:e}=n,{quota:t}=e;return!t.size}),g=c(()=>{if(f.value)return 0;let{data:e}=n,t=i(e,`quota.used`,0),r=i(e,`quota.size`,0);return r=r*1024*1024,r===0?0:t/r*100}),_=c(()=>{let{data:e}=n;return D(i(e,`quota.used`,0))}),y=c(()=>{let{data:e}=n;return`${i(e,`quota.size`,0).toFixed(2)} MB`}),b=c(()=>g.value<90?`success`:`error`),S=new Map([[`site`,`Site`],[`ftp`,`FTP`],[`database`,`Database`]]),C=()=>{E({title:`${t(`Component.Quota.index_5`,[n.data.name,S.get(n.type)||`--`])}`,width:480,minHeight:222,footer:!0,data:{type:n.type,info:n.data,callback:n.callback},component:l(()=>N(()=>Promise.resolve().then(()=>G),void 0))})};return(e,t)=>{let n=k,i=w,c=x;return u(f)?(s(),o(n,{key:0,onClick:C},{default:d(()=>[r(p(e.$t(`Component.Quota.index_2`)),1)]),_:1})):(s(),m(`div`,{key:1,class:`cursor-pointer`,onClick:C},[a(c,{placement:`bottom-start`,"arrow-point-to-center":!0},{trigger:d(()=>[a(i,{type:`line`,status:u(b),percentage:u(g),height:12,"border-radius":2,"show-indicator":!1},null,8,[`status`,`percentage`])]),default:d(()=>[h(`div`,F,[h(`p`,null,p(e.$t(`Component.Quota.index_3`,[u(_)])),1),h(`p`,null,p(e.$t(`Component.Quota.index_12`,[u(y)])),1),h(`p`,null,p(e.$t(`Component.Quota.index_4`)),1)])]),_:1})]))}}}),L=e({default:()=>R}),R=I;f();var z={class:`px-20px py-24px`},B={class:`w-160px`},V={class:`w-160px`},H={class:`text-error`},U={key:0},W=t({__name:`quota-config`,props:{data:{}},setup(e,{expose:t}){let{type:o,info:c,callback:l}=e.data,f=_({used:`0`,size:0}),v=g(`MB`);return(()=>{let e=i(c,`quota.used`,0);if(e>0){let t=D(e).split(` `);f.used=t[0],v.value=t[1]}f.size=i(c,`quota.size`,0)})(),t({onConfirm:async({hide:e})=>{(o===`site`||o===`ftp`)&&await j({size:f.size,quota_type:o,path:i(c,`path`,``)}),o===`database`&&await M({size:f.size,db_name:i(c,`name`,``)}),l==null||l(),e()}}),(e,t)=>{let i=b,c=T,l=C,g=S,_=y,x=A,w=O;return s(),m(`div`,z,[a(x,{"label-width":`180`},{default:d(()=>[a(g,{label:e.$t(`Component.Quota.index_6`)},{default:d(()=>[h(`div`,B,[a(l,null,{default:d(()=>[a(i,{value:u(f).used,"onUpdate:value":t[0]||(t[0]=e=>u(f).used=e),disabled:!0},null,8,[`value`]),a(c,{class:`w-44px text-center`},{default:d(()=>[r(p(u(v)),1)]),_:1})]),_:1})])]),_:1},8,[`label`]),a(g,{label:e.$t(`Component.Quota.index_7`)},{default:d(()=>[h(`div`,V,[a(l,null,{default:d(()=>[a(_,{value:u(f).size,"onUpdate:value":t[1]||(t[1]=e=>u(f).size=e),min:0,"show-button":!1},null,8,[`value`]),a(c,{class:`w-44px text-center`},{default:d(()=>[...t[2]||(t[2]=[r(`MB`,-1)])]),_:1})]),_:1})])]),_:1},8,[`label`])]),_:1}),a(w,{class:`mt-8px`},{default:d(()=>[h(`li`,H,p(e.$t(`Component.Quota.index_8`)),1),h(`li`,null,p(e.$t(`Component.Quota.index_9`)),1),u(o)===`database`?n(``,!0):(s(),m(`li`,U,p(e.$t(`Component.Quota.index_10`)),1)),h(`li`,null,p(e.$t(`Component.Quota.index_11`)),1)]),_:1})])}}}),G=e({default:()=>K}),K=W;export{L as t};