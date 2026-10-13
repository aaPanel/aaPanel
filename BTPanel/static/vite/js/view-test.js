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
const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["js/feature-FileEditor.js?v=1791538283700","js/rolldown-runtime.js?v=1791538283700","js/vendor-utils.js?v=1791538283700","js/vendor-vue.js?v=1791538283700","js/vendor-naive.js?v=1791538283700","js/vendor.js?v=1791538283700","css/vendor.css?v=1791538283700","js/app.js?v=1791538283700","js/vendor-pdf.js?v=1791538283700","js/vendor-polyfills.js?v=1791538283700","js/app-icons.js?v=1791538283700","css/app.css?v=1791538283700","js/app-components.js?v=1791538283700","js/app-base.js?v=1791538283700","js/vendor-code-highlight.js?v=1791538283700","css/vendor-code-highlight.css?v=1791538283700","css/app-base.css?v=1791538283700","js/vendor-pay.js?v=1791538283700","css/app-components.css?v=1791538283700","js/app-shared.js?v=1791538283700","js/app-modal-ui.js?v=1791538283700","js/vendor-crypto.js?v=1791538283700","css/app-shared.css?v=1791538283700","js/vendor-ace.js?v=1791538283700","css/vendor-ace.css?v=1791538283700","js/feature-EmailEditor.js?v=1791538283700","js/vendor-interaction.js?v=1791538283700","js/vendor-wangeditor.js?v=1791538283700","css/vendor-wangeditor.css?v=1791538283700","css/feature-EmailEditor.css?v=1791538283700","css/feature-FileEditor.css?v=1791538283700"])))=>i.map(i=>d[i]);
import{r as e}from"./rolldown-runtime.js?v=1791538283700";import{An as t,Dn as n,On as r,Yn as i,kn as a,lr as o,rn as s,wn as c}from"./vendor-utils.js?v=1791538283700";import{gt as l}from"./vendor-naive.js?v=1791538283700";import{Pf as u}from"./app.js?v=1791538283700";import{n as d,r as f}from"./vendor-pdf.js?v=1791538283700";s(),f();var p=t({__name:`index`,setup(e){let t=()=>{u({width:1430,height:744,bgColor:`transparent`,hideClose:!0,component:a(()=>d(()=>import(`./feature-FileEditor.js?v=1791538283700`).then(e=>e.t),__vite__mapDeps([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30])))})},s=()=>{t()},f=()=>{};return(e,t)=>{let a=l;return i(),c(`div`,null,[r(a,{onClick:s},{default:o(()=>[...t[0]||(t[0]=[n(`测试`,-1)])]),_:1}),r(a,{onClick:f},{default:o(()=>[...t[1]||(t[1]=[n(`消息`,-1)])]),_:1})])}}}),m=e({default:()=>h}),h=p;export{m as t};