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
import{r as e}from"./rolldown-runtime.js?v=1791538283700";import{An as t,Dn as n,On as r,Tt as i,Yn as a,hn as o,kr as s,lr as c,rn as l,ti as u,wn as d,xn as f,xr as p,yr as m}from"./vendor-utils.js?v=1791538283700";import{l as h,s as g}from"./vendor-vue.js?v=1791538283700";import{Ct as _,F as v,gt as y}from"./vendor-naive.js?v=1791538283700";import{Nf as b,Ou as x,Su as S,mn as C,pp as w}from"./app.js?v=1791538283700";import{Qi as T}from"./app-components.js?v=1791538283700";import{wf as E}from"./app-shared.js?v=1791538283700";import{c as D}from"./app-form.js?v=1791538283700";l();var O={class:`flex-center flex-col pt-8%`},k={class:`pt-44px`},A={class:`mb-24px text-center text-20p`},j={class:`flex justify-end mt-16px`},M=t({__name:`index`,setup(e){let{t}=h(),l=p(null),M=m({password1:``,password2:``,userpassword:``}),N={password1:{trigger:[`blur`,`input`],validator:()=>i(M.password1)?Error(t(`Config.Panel.index_67`)):M.password1.length<6?Error(t(`Password.index_6`)):!0},password2:{trigger:[`blur`,`input`],validator:()=>i(M.password2)?Error(t(`Config.Panel.index_69`)):M.password1===M.password2||Error(t(`Config.Panel.index_70`))},userpassword:{trigger:[`blur`,`input`],required:!0,message:t(`Config.Panel.index_67`)}},P=async()=>{var e;await((e=l.value)==null?void 0:e.validate()),await x({password1:E(M.password1),password2:E(M.password2),userpassword:E(M.userpassword)}),w(`/login?dologin=True`,1500)},F=()=>{b({title:t(`Password.index_7`),content:()=>r(o,null,[r(g,{tag:`div`,scope:`global`,keypath:`Password.index_8`},{text_1:()=>r(`span`,{class:`text-error`},[t(`Password.index_9`)])})]),onConfirm:async()=>{await S(),w(`/login?dologin=True`,1500)}})};return(e,t)=>{let i=_,o=v,p=D,m=y,h=C,g=T;return a(),d(`div`,O,[f(`div`,k,[f(`h3`,A,u(e.$t(`Password.index_1`)),1)]),r(g,{ref_key:`formRef`,ref:l,model:s(M),rules:N,size:`large`,class:`w-500px p-32px pt-0`},{default:c(()=>[r(o,{path:`userpassword`},{default:c(()=>[r(i,{value:s(M).userpassword,"onUpdate:value":t[0]||(t[0]=e=>s(M).userpassword=e),placeholder:e.$t(`Old Password`)},null,8,[`value`,`placeholder`])]),_:1}),r(o,{path:`password1`},{default:c(()=>[r(p,{value:s(M).password1,"onUpdate:value":t[1]||(t[1]=e=>s(M).password1=e),length:10,default:!1,placeholder:e.$t(`Password.index_2`)},null,8,[`value`,`placeholder`])]),_:1}),r(o,{path:`password2`},{default:c(()=>[r(i,{value:s(M).password2,"onUpdate:value":t[2]||(t[2]=e=>s(M).password2=e),placeholder:e.$t(`Password.index_3`)},null,8,[`value`,`placeholder`])]),_:1}),r(o,{"show-feedback":!1},{default:c(()=>[r(m,{type:`primary`,block:``,onClick:P},{default:c(()=>[n(u(e.$t(`Password.index_4`)),1)]),_:1})]),_:1}),f(`div`,j,[r(h,{onClick:F},{default:c(()=>[n(u(e.$t(`Password.index_5`)),1)]),_:1})])]),_:1},8,[`model`])])}}}),N=e({default:()=>P}),P=M;export{N as t};