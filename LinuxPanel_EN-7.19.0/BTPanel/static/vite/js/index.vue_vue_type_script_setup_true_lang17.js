import{f as a}from"./page_layout.js?v=1732601582185";import{aI as e}from"./site.js?v=1732601582185";import{b as s}from"./public.js?v=1732601582185";import{d as t,aq as o,r as l,O as i,X as r,u as n,R as u}from"./vue.js?v=1732601582185";import{bL as p}from"./naive.js?v=1732601582185";const m=t({__name:"index",props:{value:{},valueModifiers:{}},emits:["update:value"],setup(t){const m=o(t,"value"),{loading:v,setLoading:d}=s(),f=l([]);return(async()=>{try{d(!0);const{message:s}=await e();a(s)&&(f.value=Object.entries(s).map((([a,e])=>({label:e,value:a}))))}finally{d(!1)}})(),(a,e)=>{const s=p;return i(),r(s,n({value:m.value,"onUpdate:value":e[0]||(e[0]=a=>m.value=a),loading:u(v),filterable:"",options:u(f)},a.$attrs),null,16,["value","loading","options"])}}});export{m as _};