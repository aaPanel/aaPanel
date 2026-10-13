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
import{r as e}from"./rolldown-runtime.js?v=1791538283700";import{An as t,On as n,Yn as r,kr as i,rn as a,ti as o,wn as s,xn as c}from"./vendor-utils.js?v=1791538283700";import{c as l,l as u,s as d,t as f,u as p}from"./view-mail.js?v=1791538283700";a();var m={class:`p-40px`},h=t({__name:`index`,setup(e){return(e,t)=>(r(),s(`div`,m,[c(`div`,null,` columns_source:`+o(i(u)),1),c(`div`,null,` column_map:`+o(i(l)),1),c(`div`,null,` cell_map:`+o(i(d)),1),c(`div`,null,` comp_map:`+o(i(p)),1),n(f)]))}}),g=e({default:()=>_}),_=h;export{g as t};