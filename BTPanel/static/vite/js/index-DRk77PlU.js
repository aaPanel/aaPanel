function n(r=12){const t=new Uint8Array(r);return crypto.getRandomValues(t),Array.from(t,a=>a.toString(16).padStart(2,"0")).join("").slice(0,r)}export{n as g};
