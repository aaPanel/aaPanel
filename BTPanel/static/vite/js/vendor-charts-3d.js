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
import{$ as e,At as t,B as n,Ct as r,Dt as i,Et as a,F as o,G as s,H as c,I as l,J as u,K as d,L as f,M as p,Mt as m,N as h,Nt as g,Ot as _,P as v,Q as y,R as b,St as x,T as S,Tt as C,V as w,W as T,X as E,Y as D,Z as O,_t as k,at as A,bt as j,ct as M,dt as N,et as ee,ft as te,gt as P,ht as ne,it as re,j as ie,jt as ae,kt as F,lt as oe,mt as se,n as ce,nt as le,ot as ue,pt as de,q as fe,r as pe,rt as me,st as he,t as ge,tt as _e,ut as ve,vt as ye,w as be,wt as xe,x as Se,xt as Ce,yt as we,z as Te}from"./vendor-charts.js?v=1791538283700";function Ee(e,t,n){typeof t==`object`&&(n=t,t=null);var r=this,i;if(!(e instanceof Function))for(var a in i=[],e)e.hasOwnProperty(a)&&i.push(a);var o=function(t){if(r.apply(this,arguments),e instanceof Function?De(this,e.call(this,t)):Oe(this,e,i),this.constructor===o)for(var n=o.__initializers__,a=0;a<n.length;a++)n[a].apply(this,arguments)};o.__super__=r,r.__initializers__?o.__initializers__=r.__initializers__.slice():o.__initializers__=[],t&&o.__initializers__.push(t);var s=function(){};return s.prototype=r.prototype,o.prototype=new s,o.prototype.constructor=o,De(o.prototype,n),o.extend=r.extend,o.derive=r.extend,o}function De(e,t){if(t)for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])}function Oe(e,t,n){for(var r=0;r<n.length;r++){var i=n[r];e[i]=t[i]}}var ke={extend:Ee,derive:Ee};function Ae(e,t){this.action=e,this.context=t}var je={trigger:function(e){if(this.hasOwnProperty(`__handlers__`)&&this.__handlers__.hasOwnProperty(e)){var t=this.__handlers__[e],n=t.length,r=-1,i=arguments;switch(i.length){case 1:for(;++r<n;)t[r].action.call(t[r].context);return;case 2:for(;++r<n;)t[r].action.call(t[r].context,i[1]);return;case 3:for(;++r<n;)t[r].action.call(t[r].context,i[1],i[2]);return;case 4:for(;++r<n;)t[r].action.call(t[r].context,i[1],i[2],i[3]);return;case 5:for(;++r<n;)t[r].action.call(t[r].context,i[1],i[2],i[3],i[4]);return;default:for(;++r<n;)t[r].action.apply(t[r].context,Array.prototype.slice.call(i,1));return}}},on:function(e,t,n){if(!(!e||!t)){var r=this.__handlers__||(this.__handlers__={});if(!r[e])r[e]=[];else if(this.has(e,t))return;var i=new Ae(t,n||this);return r[e].push(i),this}},once:function(e,t,n){if(!e||!t)return;var r=this;function i(){r.off(e,i),t.apply(this,arguments)}return this.on(e,i,n)},before:function(e,t,n){if(!(!e||!t))return e=`before`+e,this.on(e,t,n)},after:function(e,t,n){if(!(!e||!t))return e=`after`+e,this.on(e,t,n)},success:function(e,t){return this.once(`success`,e,t)},error:function(e,t){return this.once(`error`,e,t)},off:function(e,t){var n=this.__handlers__||(this.__handlers__={});if(!t){n[e]=[];return}if(n[e]){for(var r=n[e],i=[],a=0;a<r.length;a++)t&&r[a].action!==t&&i.push(r[a]);n[e]=i}return this},has:function(e,t){var n=this.__handlers__;if(!n||!n[e])return!1;for(var r=n[e],i=0;i<r.length;i++)if(r[i].action===t)return!0}},Me=0,Ne=Array.prototype.forEach,Pe={genGUID:function(){return++Me},relative2absolute:function(e,t){if(!t||e.match(/^\//))return e;for(var n=e.split(`/`),r=t.split(`/`),i=n[0];i===`.`||i===`..`;)i===`..`&&r.pop(),n.shift(),i=n[0];return r.join(`/`)+`/`+n.join(`/`)},extend:function(e,t){if(t)for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n]);return e},defaults:function(e,t){if(t)for(var n in t)e[n]===void 0&&(e[n]=t[n]);return e},extendWithPropList:function(e,t,n){if(t)for(var r=0;r<n.length;r++){var i=n[r];e[i]=t[i]}return e},defaultsWithPropList:function(e,t,n){if(t)for(var r=0;r<n.length;r++){var i=n[r];e[i]==null&&(e[i]=t[i])}return e},each:function(e,t,n){if(e&&t)if(e.forEach&&e.forEach===Ne)e.forEach(t,n);else if(e.length===+e.length)for(var r=0,i=e.length;r<i;r++)t.call(n,e[r],r,e);else for(var a in e)e.hasOwnProperty(a)&&t.call(n,e[a],a,e)},isObject:function(e){return e===Object(e)},isArray:function(e){return Array.isArray(e)},isArrayLike:function(e){return e?e.length===+e.length:!1},clone:function(e){if(!Pe.isObject(e))return e;if(Pe.isArray(e))return e.slice();if(Pe.isArrayLike(e)){for(var t=new e.constructor(e.length),n=0;n<e.length;n++)t[n]=e[n];return t}else return Pe.extend({},e)}},Fe=function(){this.__uid__=Pe.genGUID()};Fe.__initializers__=[function(e){Pe.extend(this,e)}],Pe.extend(Fe,ke),Pe.extend(Fe.prototype,je);var Ie=Array,Le=Math.random,I={};I.create=function(){var e=new Ie(3);return e[0]=0,e[1]=0,e[2]=0,e},I.clone=function(e){var t=new Ie(3);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t},I.fromValues=function(e,t,n){var r=new Ie(3);return r[0]=e,r[1]=t,r[2]=n,r},I.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e},I.set=function(e,t,n,r){return e[0]=t,e[1]=n,e[2]=r,e},I.add=function(e,t,n){return e[0]=t[0]+n[0],e[1]=t[1]+n[1],e[2]=t[2]+n[2],e},I.subtract=function(e,t,n){return e[0]=t[0]-n[0],e[1]=t[1]-n[1],e[2]=t[2]-n[2],e},I.sub=I.subtract,I.multiply=function(e,t,n){return e[0]=t[0]*n[0],e[1]=t[1]*n[1],e[2]=t[2]*n[2],e},I.mul=I.multiply,I.divide=function(e,t,n){return e[0]=t[0]/n[0],e[1]=t[1]/n[1],e[2]=t[2]/n[2],e},I.div=I.divide,I.min=function(e,t,n){return e[0]=Math.min(t[0],n[0]),e[1]=Math.min(t[1],n[1]),e[2]=Math.min(t[2],n[2]),e},I.max=function(e,t,n){return e[0]=Math.max(t[0],n[0]),e[1]=Math.max(t[1],n[1]),e[2]=Math.max(t[2],n[2]),e},I.scale=function(e,t,n){return e[0]=t[0]*n,e[1]=t[1]*n,e[2]=t[2]*n,e},I.scaleAndAdd=function(e,t,n,r){return e[0]=t[0]+n[0]*r,e[1]=t[1]+n[1]*r,e[2]=t[2]+n[2]*r,e},I.distance=function(e,t){var n=t[0]-e[0],r=t[1]-e[1],i=t[2]-e[2];return Math.sqrt(n*n+r*r+i*i)},I.dist=I.distance,I.squaredDistance=function(e,t){var n=t[0]-e[0],r=t[1]-e[1],i=t[2]-e[2];return n*n+r*r+i*i},I.sqrDist=I.squaredDistance,I.length=function(e){var t=e[0],n=e[1],r=e[2];return Math.sqrt(t*t+n*n+r*r)},I.len=I.length,I.squaredLength=function(e){var t=e[0],n=e[1],r=e[2];return t*t+n*n+r*r},I.sqrLen=I.squaredLength,I.negate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e[2]=-t[2],e},I.inverse=function(e,t){return e[0]=1/t[0],e[1]=1/t[1],e[2]=1/t[2],e},I.normalize=function(e,t){var n=t[0],r=t[1],i=t[2],a=n*n+r*r+i*i;return a>0&&(a=1/Math.sqrt(a),e[0]=t[0]*a,e[1]=t[1]*a,e[2]=t[2]*a),e},I.dot=function(e,t){return e[0]*t[0]+e[1]*t[1]+e[2]*t[2]},I.cross=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=n[0],s=n[1],c=n[2];return e[0]=i*c-a*s,e[1]=a*o-r*c,e[2]=r*s-i*o,e},I.lerp=function(e,t,n,r){var i=t[0],a=t[1],o=t[2];return e[0]=i+r*(n[0]-i),e[1]=a+r*(n[1]-a),e[2]=o+r*(n[2]-o),e},I.random=function(e,t){t=t||1;var n=Le()*2*Math.PI,r=Le()*2-1,i=Math.sqrt(1-r*r)*t;return e[0]=Math.cos(n)*i,e[1]=Math.sin(n)*i,e[2]=r*t,e},I.transformMat4=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=n[3]*r+n[7]*i+n[11]*a+n[15];return o=o||1,e[0]=(n[0]*r+n[4]*i+n[8]*a+n[12])/o,e[1]=(n[1]*r+n[5]*i+n[9]*a+n[13])/o,e[2]=(n[2]*r+n[6]*i+n[10]*a+n[14])/o,e},I.transformMat3=function(e,t,n){var r=t[0],i=t[1],a=t[2];return e[0]=r*n[0]+i*n[3]+a*n[6],e[1]=r*n[1]+i*n[4]+a*n[7],e[2]=r*n[2]+i*n[5]+a*n[8],e},I.transformQuat=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=n[0],s=n[1],c=n[2],l=n[3],u=l*r+s*a-c*i,d=l*i+c*r-o*a,f=l*a+o*i-s*r,p=-o*r-s*i-c*a;return e[0]=u*l+p*-o+d*-c-f*-s,e[1]=d*l+p*-s+f*-o-u*-c,e[2]=f*l+p*-c+u*-s-d*-o,e},I.rotateX=function(e,t,n,r){var i=[],a=[];return i[0]=t[0]-n[0],i[1]=t[1]-n[1],i[2]=t[2]-n[2],a[0]=i[0],a[1]=i[1]*Math.cos(r)-i[2]*Math.sin(r),a[2]=i[1]*Math.sin(r)+i[2]*Math.cos(r),e[0]=a[0]+n[0],e[1]=a[1]+n[1],e[2]=a[2]+n[2],e},I.rotateY=function(e,t,n,r){var i=[],a=[];return i[0]=t[0]-n[0],i[1]=t[1]-n[1],i[2]=t[2]-n[2],a[0]=i[2]*Math.sin(r)+i[0]*Math.cos(r),a[1]=i[1],a[2]=i[2]*Math.cos(r)-i[0]*Math.sin(r),e[0]=a[0]+n[0],e[1]=a[1]+n[1],e[2]=a[2]+n[2],e},I.rotateZ=function(e,t,n,r){var i=[],a=[];return i[0]=t[0]-n[0],i[1]=t[1]-n[1],i[2]=t[2]-n[2],a[0]=i[0]*Math.cos(r)-i[1]*Math.sin(r),a[1]=i[0]*Math.sin(r)+i[1]*Math.cos(r),a[2]=i[2],e[0]=a[0]+n[0],e[1]=a[1]+n[1],e[2]=a[2]+n[2],e},I.forEach=(function(){var e=I.create();return function(t,n,r,i,a,o){var s,c;for(n||(n=3),r||(r=0),c=i?Math.min(i*n+r,t.length):t.length,s=r;s<c;s+=n)e[0]=t[s],e[1]=t[s+1],e[2]=t[s+2],a(e,e,o),t[s]=e[0],t[s+1]=e[1],t[s+2]=e[2];return t}})(),I.angle=function(e,t){var n=I.fromValues(e[0],e[1],e[2]),r=I.fromValues(t[0],t[1],t[2]);I.normalize(n,n),I.normalize(r,r);var i=I.dot(n,r);return i>1?0:Math.acos(i)};var L=function(e,t,n){e=e||0,t=t||0,n=n||0,this.array=I.fromValues(e,t,n),this._dirty=!0};L.prototype={constructor:L,add:function(e){return I.add(this.array,this.array,e.array),this._dirty=!0,this},set:function(e,t,n){return this.array[0]=e,this.array[1]=t,this.array[2]=n,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this.array[2]=e[2],this._dirty=!0,this},clone:function(){return new L(this.x,this.y,this.z)},copy:function(e){return I.copy(this.array,e.array),this._dirty=!0,this},cross:function(e,t){return I.cross(this.array,e.array,t.array),this._dirty=!0,this},dist:function(e){return I.dist(this.array,e.array)},distance:function(e){return I.distance(this.array,e.array)},div:function(e){return I.div(this.array,this.array,e.array),this._dirty=!0,this},divide:function(e){return I.divide(this.array,this.array,e.array),this._dirty=!0,this},dot:function(e){return I.dot(this.array,e.array)},len:function(){return I.len(this.array)},length:function(){return I.length(this.array)},lerp:function(e,t,n){return I.lerp(this.array,e.array,t.array,n),this._dirty=!0,this},min:function(e){return I.min(this.array,this.array,e.array),this._dirty=!0,this},max:function(e){return I.max(this.array,this.array,e.array),this._dirty=!0,this},mul:function(e){return I.mul(this.array,this.array,e.array),this._dirty=!0,this},multiply:function(e){return I.multiply(this.array,this.array,e.array),this._dirty=!0,this},negate:function(){return I.negate(this.array,this.array),this._dirty=!0,this},normalize:function(){return I.normalize(this.array,this.array),this._dirty=!0,this},random:function(e){return I.random(this.array,e),this._dirty=!0,this},scale:function(e){return I.scale(this.array,this.array,e),this._dirty=!0,this},scaleAndAdd:function(e,t){return I.scaleAndAdd(this.array,this.array,e.array,t),this._dirty=!0,this},sqrDist:function(e){return I.sqrDist(this.array,e.array)},squaredDistance:function(e){return I.squaredDistance(this.array,e.array)},sqrLen:function(){return I.sqrLen(this.array)},squaredLength:function(){return I.squaredLength(this.array)},sub:function(e){return I.sub(this.array,this.array,e.array),this._dirty=!0,this},subtract:function(e){return I.subtract(this.array,this.array,e.array),this._dirty=!0,this},transformMat3:function(e){return I.transformMat3(this.array,this.array,e.array),this._dirty=!0,this},transformMat4:function(e){return I.transformMat4(this.array,this.array,e.array),this._dirty=!0,this},transformQuat:function(e){return I.transformQuat(this.array,this.array,e.array),this._dirty=!0,this},applyProjection:function(e){var t=this.array;if(e=e.array,e[15]===0){var n=-1/t[2];t[0]=e[0]*t[0]*n,t[1]=e[5]*t[1]*n,t[2]=(e[10]*t[2]+e[14])*n}else t[0]=e[0]*t[0]+e[12],t[1]=e[5]*t[1]+e[13],t[2]=e[10]*t[2]+e[14];return this._dirty=!0,this},eulerFromQuat:function(e,t){L.eulerFromQuat(this,e,t)},eulerFromMat3:function(e,t){L.eulerFromMat3(this,e,t)},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}};var Re=Object.defineProperty;if(Re){var ze=L.prototype;Re(ze,`x`,{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),Re(ze,`y`,{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}}),Re(ze,`z`,{get:function(){return this.array[2]},set:function(e){this.array[2]=e,this._dirty=!0}})}L.add=function(e,t,n){return I.add(e.array,t.array,n.array),e._dirty=!0,e},L.set=function(e,t,n,r){I.set(e.array,t,n,r),e._dirty=!0},L.copy=function(e,t){return I.copy(e.array,t.array),e._dirty=!0,e},L.cross=function(e,t,n){return I.cross(e.array,t.array,n.array),e._dirty=!0,e},L.dist=function(e,t){return I.distance(e.array,t.array)},L.distance=L.dist,L.div=function(e,t,n){return I.divide(e.array,t.array,n.array),e._dirty=!0,e},L.divide=L.div,L.dot=function(e,t){return I.dot(e.array,t.array)},L.len=function(e){return I.length(e.array)},L.lerp=function(e,t,n,r){return I.lerp(e.array,t.array,n.array,r),e._dirty=!0,e},L.min=function(e,t,n){return I.min(e.array,t.array,n.array),e._dirty=!0,e},L.max=function(e,t,n){return I.max(e.array,t.array,n.array),e._dirty=!0,e},L.mul=function(e,t,n){return I.multiply(e.array,t.array,n.array),e._dirty=!0,e},L.multiply=L.mul,L.negate=function(e,t){return I.negate(e.array,t.array),e._dirty=!0,e},L.normalize=function(e,t){return I.normalize(e.array,t.array),e._dirty=!0,e},L.random=function(e,t){return I.random(e.array,t),e._dirty=!0,e},L.scale=function(e,t,n){return I.scale(e.array,t.array,n),e._dirty=!0,e},L.scaleAndAdd=function(e,t,n,r){return I.scaleAndAdd(e.array,t.array,n.array,r),e._dirty=!0,e},L.sqrDist=function(e,t){return I.sqrDist(e.array,t.array)},L.squaredDistance=L.sqrDist,L.sqrLen=function(e){return I.sqrLen(e.array)},L.squaredLength=L.sqrLen,L.sub=function(e,t,n){return I.subtract(e.array,t.array,n.array),e._dirty=!0,e},L.subtract=L.sub,L.transformMat3=function(e,t,n){return I.transformMat3(e.array,t.array,n.array),e._dirty=!0,e},L.transformMat4=function(e,t,n){return I.transformMat4(e.array,t.array,n.array),e._dirty=!0,e},L.transformQuat=function(e,t,n){return I.transformQuat(e.array,t.array,n.array),e._dirty=!0,e};function Be(e,t,n){return e<t?t:e>n?n:e}var Ve=Math.atan2,He=Math.asin,Ue=Math.abs;L.eulerFromQuat=function(e,t,n){e._dirty=!0,t=t.array;var r=e.array,i=t[0],a=t[1],o=t[2],s=t[3],c=i*i,l=a*a,u=o*o,d=s*s,n=(n||`XYZ`).toUpperCase();switch(n){case`XYZ`:r[0]=Ve(2*(i*s-a*o),d-c-l+u),r[1]=He(Be(2*(i*o+a*s),-1,1)),r[2]=Ve(2*(o*s-i*a),d+c-l-u);break;case`YXZ`:r[0]=He(Be(2*(i*s-a*o),-1,1)),r[1]=Ve(2*(i*o+a*s),d-c-l+u),r[2]=Ve(2*(i*a+o*s),d-c+l-u);break;case`ZXY`:r[0]=He(Be(2*(i*s+a*o),-1,1)),r[1]=Ve(2*(a*s-o*i),d-c-l+u),r[2]=Ve(2*(o*s-i*a),d-c+l-u);break;case`ZYX`:r[0]=Ve(2*(i*s+o*a),d-c-l+u),r[1]=He(Be(2*(a*s-i*o),-1,1)),r[2]=Ve(2*(i*a+o*s),d+c-l-u);break;case`YZX`:r[0]=Ve(2*(i*s-o*a),d-c+l-u),r[1]=Ve(2*(a*s-i*o),d+c-l-u),r[2]=He(Be(2*(i*a+o*s),-1,1));break;case`XZY`:r[0]=Ve(2*(i*s+a*o),d-c+l-u),r[1]=Ve(2*(i*o+a*s),d+c-l-u),r[2]=He(Be(2*(o*s-i*a),-1,1));break;default:console.warn(`Unkown order: `+n)}return e},L.eulerFromMat3=function(e,t,n){var r=t.array,i=r[0],a=r[3],o=r[6],s=r[1],c=r[4],l=r[7],u=r[2],d=r[5],f=r[8],p=e.array,n=(n||`XYZ`).toUpperCase();switch(n){case`XYZ`:p[1]=He(Be(o,-1,1)),Ue(o)<.99999?(p[0]=Ve(-l,f),p[2]=Ve(-a,i)):(p[0]=Ve(d,c),p[2]=0);break;case`YXZ`:p[0]=He(-Be(l,-1,1)),Ue(l)<.99999?(p[1]=Ve(o,f),p[2]=Ve(s,c)):(p[1]=Ve(-u,i),p[2]=0);break;case`ZXY`:p[0]=He(Be(d,-1,1)),Ue(d)<.99999?(p[1]=Ve(-u,f),p[2]=Ve(-a,c)):(p[1]=0,p[2]=Ve(s,i));break;case`ZYX`:p[1]=He(-Be(u,-1,1)),Ue(u)<.99999?(p[0]=Ve(d,f),p[2]=Ve(s,i)):(p[0]=0,p[2]=Ve(-a,c));break;case`YZX`:p[2]=He(Be(s,-1,1)),Ue(s)<.99999?(p[0]=Ve(-l,c),p[1]=Ve(-u,i)):(p[0]=0,p[1]=Ve(o,f));break;case`XZY`:p[2]=He(-Be(a,-1,1)),Ue(a)<.99999?(p[0]=Ve(d,c),p[1]=Ve(o,i)):(p[0]=Ve(-l,f),p[1]=0);break;default:console.warn(`Unkown order: `+n)}return e._dirty=!0,e},Object.defineProperties(L,{POSITIVE_X:{get:function(){return new L(1,0,0)}},NEGATIVE_X:{get:function(){return new L(-1,0,0)}},POSITIVE_Y:{get:function(){return new L(0,1,0)}},NEGATIVE_Y:{get:function(){return new L(0,-1,0)}},POSITIVE_Z:{get:function(){return new L(0,0,1)}},NEGATIVE_Z:{get:function(){return new L(0,0,-1)}},UP:{get:function(){return new L(0,1,0)}},ZERO:{get:function(){return new L}}});var R={};R.create=function(){var e=new Ie(4);return e[0]=0,e[1]=0,e[2]=0,e[3]=0,e},R.clone=function(e){var t=new Ie(4);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t},R.fromValues=function(e,t,n,r){var i=new Ie(4);return i[0]=e,i[1]=t,i[2]=n,i[3]=r,i},R.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e},R.set=function(e,t,n,r,i){return e[0]=t,e[1]=n,e[2]=r,e[3]=i,e},R.add=function(e,t,n){return e[0]=t[0]+n[0],e[1]=t[1]+n[1],e[2]=t[2]+n[2],e[3]=t[3]+n[3],e},R.subtract=function(e,t,n){return e[0]=t[0]-n[0],e[1]=t[1]-n[1],e[2]=t[2]-n[2],e[3]=t[3]-n[3],e},R.sub=R.subtract,R.multiply=function(e,t,n){return e[0]=t[0]*n[0],e[1]=t[1]*n[1],e[2]=t[2]*n[2],e[3]=t[3]*n[3],e},R.mul=R.multiply,R.divide=function(e,t,n){return e[0]=t[0]/n[0],e[1]=t[1]/n[1],e[2]=t[2]/n[2],e[3]=t[3]/n[3],e},R.div=R.divide,R.min=function(e,t,n){return e[0]=Math.min(t[0],n[0]),e[1]=Math.min(t[1],n[1]),e[2]=Math.min(t[2],n[2]),e[3]=Math.min(t[3],n[3]),e},R.max=function(e,t,n){return e[0]=Math.max(t[0],n[0]),e[1]=Math.max(t[1],n[1]),e[2]=Math.max(t[2],n[2]),e[3]=Math.max(t[3],n[3]),e},R.scale=function(e,t,n){return e[0]=t[0]*n,e[1]=t[1]*n,e[2]=t[2]*n,e[3]=t[3]*n,e},R.scaleAndAdd=function(e,t,n,r){return e[0]=t[0]+n[0]*r,e[1]=t[1]+n[1]*r,e[2]=t[2]+n[2]*r,e[3]=t[3]+n[3]*r,e},R.distance=function(e,t){var n=t[0]-e[0],r=t[1]-e[1],i=t[2]-e[2],a=t[3]-e[3];return Math.sqrt(n*n+r*r+i*i+a*a)},R.dist=R.distance,R.squaredDistance=function(e,t){var n=t[0]-e[0],r=t[1]-e[1],i=t[2]-e[2],a=t[3]-e[3];return n*n+r*r+i*i+a*a},R.sqrDist=R.squaredDistance,R.length=function(e){var t=e[0],n=e[1],r=e[2],i=e[3];return Math.sqrt(t*t+n*n+r*r+i*i)},R.len=R.length,R.squaredLength=function(e){var t=e[0],n=e[1],r=e[2],i=e[3];return t*t+n*n+r*r+i*i},R.sqrLen=R.squaredLength,R.negate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e[2]=-t[2],e[3]=-t[3],e},R.inverse=function(e,t){return e[0]=1/t[0],e[1]=1/t[1],e[2]=1/t[2],e[3]=1/t[3],e},R.normalize=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=n*n+r*r+i*i+a*a;return o>0&&(o=1/Math.sqrt(o),e[0]=t[0]*o,e[1]=t[1]*o,e[2]=t[2]*o,e[3]=t[3]*o),e},R.dot=function(e,t){return e[0]*t[0]+e[1]*t[1]+e[2]*t[2]+e[3]*t[3]},R.lerp=function(e,t,n,r){var i=t[0],a=t[1],o=t[2],s=t[3];return e[0]=i+r*(n[0]-i),e[1]=a+r*(n[1]-a),e[2]=o+r*(n[2]-o),e[3]=s+r*(n[3]-s),e},R.random=function(e,t){return t=t||1,e[0]=Le(),e[1]=Le(),e[2]=Le(),e[3]=Le(),R.normalize(e,e),R.scale(e,e,t),e},R.transformMat4=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3];return e[0]=n[0]*r+n[4]*i+n[8]*a+n[12]*o,e[1]=n[1]*r+n[5]*i+n[9]*a+n[13]*o,e[2]=n[2]*r+n[6]*i+n[10]*a+n[14]*o,e[3]=n[3]*r+n[7]*i+n[11]*a+n[15]*o,e},R.transformQuat=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=n[0],s=n[1],c=n[2],l=n[3],u=l*r+s*a-c*i,d=l*i+c*r-o*a,f=l*a+o*i-s*r,p=-o*r-s*i-c*a;return e[0]=u*l+p*-o+d*-c-f*-s,e[1]=d*l+p*-s+f*-o-u*-c,e[2]=f*l+p*-c+u*-s-d*-o,e},R.forEach=(function(){var e=R.create();return function(t,n,r,i,a,o){var s,c;for(n||(n=4),r||(r=0),c=i?Math.min(i*n+r,t.length):t.length,s=r;s<c;s+=n)e[0]=t[s],e[1]=t[s+1],e[2]=t[s+2],e[3]=t[s+3],a(e,e,o),t[s]=e[0],t[s+1]=e[1],t[s+2]=e[2],t[s+3]=e[3];return t}})();var z={};z.create=function(){var e=new Ie(9);return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=1,e[5]=0,e[6]=0,e[7]=0,e[8]=1,e},z.fromMat4=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[4],e[4]=t[5],e[5]=t[6],e[6]=t[8],e[7]=t[9],e[8]=t[10],e},z.clone=function(e){var t=new Ie(9);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t[4]=e[4],t[5]=e[5],t[6]=e[6],t[7]=e[7],t[8]=e[8],t},z.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e[6]=t[6],e[7]=t[7],e[8]=t[8],e},z.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=1,e[5]=0,e[6]=0,e[7]=0,e[8]=1,e},z.transpose=function(e,t){if(e===t){var n=t[1],r=t[2],i=t[5];e[1]=t[3],e[2]=t[6],e[3]=n,e[5]=t[7],e[6]=r,e[7]=i}else e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8];return e},z.invert=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=t[4],s=t[5],c=t[6],l=t[7],u=t[8],d=u*o-s*l,f=-u*a+s*c,p=l*a-o*c,m=n*d+r*f+i*p;return m?(m=1/m,e[0]=d*m,e[1]=(-u*r+i*l)*m,e[2]=(s*r-i*o)*m,e[3]=f*m,e[4]=(u*n-i*c)*m,e[5]=(-s*n+i*a)*m,e[6]=p*m,e[7]=(-l*n+r*c)*m,e[8]=(o*n-r*a)*m,e):null},z.adjoint=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=t[4],s=t[5],c=t[6],l=t[7],u=t[8];return e[0]=o*u-s*l,e[1]=i*l-r*u,e[2]=r*s-i*o,e[3]=s*c-a*u,e[4]=n*u-i*c,e[5]=i*a-n*s,e[6]=a*l-o*c,e[7]=r*c-n*l,e[8]=n*o-r*a,e},z.determinant=function(e){var t=e[0],n=e[1],r=e[2],i=e[3],a=e[4],o=e[5],s=e[6],c=e[7],l=e[8];return t*(l*a-o*c)+n*(-l*i+o*s)+r*(c*i-a*s)},z.multiply=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=t[6],u=t[7],d=t[8],f=n[0],p=n[1],m=n[2],h=n[3],g=n[4],_=n[5],v=n[6],y=n[7],b=n[8];return e[0]=f*r+p*o+m*l,e[1]=f*i+p*s+m*u,e[2]=f*a+p*c+m*d,e[3]=h*r+g*o+_*l,e[4]=h*i+g*s+_*u,e[5]=h*a+g*c+_*d,e[6]=v*r+y*o+b*l,e[7]=v*i+y*s+b*u,e[8]=v*a+y*c+b*d,e},z.mul=z.multiply,z.translate=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=t[6],u=t[7],d=t[8],f=n[0],p=n[1];return e[0]=r,e[1]=i,e[2]=a,e[3]=o,e[4]=s,e[5]=c,e[6]=f*r+p*o+l,e[7]=f*i+p*s+u,e[8]=f*a+p*c+d,e},z.rotate=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=t[6],u=t[7],d=t[8],f=Math.sin(n),p=Math.cos(n);return e[0]=p*r+f*o,e[1]=p*i+f*s,e[2]=p*a+f*c,e[3]=p*o-f*r,e[4]=p*s-f*i,e[5]=p*c-f*a,e[6]=l,e[7]=u,e[8]=d,e},z.scale=function(e,t,n){var r=n[0],i=n[1];return e[0]=r*t[0],e[1]=r*t[1],e[2]=r*t[2],e[3]=i*t[3],e[4]=i*t[4],e[5]=i*t[5],e[6]=t[6],e[7]=t[7],e[8]=t[8],e},z.fromMat2d=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=0,e[3]=t[2],e[4]=t[3],e[5]=0,e[6]=t[4],e[7]=t[5],e[8]=1,e},z.fromQuat=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=n+n,s=r+r,c=i+i,l=n*o,u=r*o,d=r*s,f=i*o,p=i*s,m=i*c,h=a*o,g=a*s,_=a*c;return e[0]=1-d-m,e[3]=u-_,e[6]=f+g,e[1]=u+_,e[4]=1-l-m,e[7]=p-h,e[2]=f-g,e[5]=p+h,e[8]=1-l-d,e},z.normalFromMat4=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=t[4],s=t[5],c=t[6],l=t[7],u=t[8],d=t[9],f=t[10],p=t[11],m=t[12],h=t[13],g=t[14],_=t[15],v=n*s-r*o,y=n*c-i*o,b=n*l-a*o,x=r*c-i*s,S=r*l-a*s,C=i*l-a*c,w=u*h-d*m,T=u*g-f*m,E=u*_-p*m,D=d*g-f*h,O=d*_-p*h,k=f*_-p*g,A=v*k-y*O+b*D+x*E-S*T+C*w;return A?(A=1/A,e[0]=(s*k-c*O+l*D)*A,e[1]=(c*E-o*k-l*T)*A,e[2]=(o*O-s*E+l*w)*A,e[3]=(i*O-r*k-a*D)*A,e[4]=(n*k-i*E+a*T)*A,e[5]=(r*E-n*O-a*w)*A,e[6]=(h*C-g*S+_*x)*A,e[7]=(g*b-m*C-_*y)*A,e[8]=(m*S-h*b+_*v)*A,e):null},z.frob=function(e){return Math.sqrt(e[0]**2+e[1]**2+e[2]**2+e[3]**2+e[4]**2+e[5]**2+e[6]**2+e[7]**2+e[8]**2)};var B={};B.create=function(){var e=new Ie(4);return e[0]=0,e[1]=0,e[2]=0,e[3]=1,e},B.rotationTo=(function(){var e=I.create(),t=I.fromValues(1,0,0),n=I.fromValues(0,1,0);return function(r,i,a){var o=I.dot(i,a);return o<-.999999?(I.cross(e,t,i),I.length(e)<1e-6&&I.cross(e,n,i),I.normalize(e,e),B.setAxisAngle(r,e,Math.PI),r):o>.999999?(r[0]=0,r[1]=0,r[2]=0,r[3]=1,r):(I.cross(e,i,a),r[0]=e[0],r[1]=e[1],r[2]=e[2],r[3]=1+o,B.normalize(r,r))}})(),B.setAxes=(function(){var e=z.create();return function(t,n,r,i){return e[0]=r[0],e[3]=r[1],e[6]=r[2],e[1]=i[0],e[4]=i[1],e[7]=i[2],e[2]=-n[0],e[5]=-n[1],e[8]=-n[2],B.normalize(t,B.fromMat3(t,e))}})(),B.clone=R.clone,B.fromValues=R.fromValues,B.copy=R.copy,B.set=R.set,B.identity=function(e){return e[0]=0,e[1]=0,e[2]=0,e[3]=1,e},B.setAxisAngle=function(e,t,n){n*=.5;var r=Math.sin(n);return e[0]=r*t[0],e[1]=r*t[1],e[2]=r*t[2],e[3]=Math.cos(n),e},B.add=R.add,B.multiply=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=n[0],c=n[1],l=n[2],u=n[3];return e[0]=r*u+o*s+i*l-a*c,e[1]=i*u+o*c+a*s-r*l,e[2]=a*u+o*l+r*c-i*s,e[3]=o*u-r*s-i*c-a*l,e},B.mul=B.multiply,B.scale=R.scale,B.rotateX=function(e,t,n){n*=.5;var r=t[0],i=t[1],a=t[2],o=t[3],s=Math.sin(n),c=Math.cos(n);return e[0]=r*c+o*s,e[1]=i*c+a*s,e[2]=a*c-i*s,e[3]=o*c-r*s,e},B.rotateY=function(e,t,n){n*=.5;var r=t[0],i=t[1],a=t[2],o=t[3],s=Math.sin(n),c=Math.cos(n);return e[0]=r*c-a*s,e[1]=i*c+o*s,e[2]=a*c+r*s,e[3]=o*c-i*s,e},B.rotateZ=function(e,t,n){n*=.5;var r=t[0],i=t[1],a=t[2],o=t[3],s=Math.sin(n),c=Math.cos(n);return e[0]=r*c+i*s,e[1]=i*c-r*s,e[2]=a*c+o*s,e[3]=o*c-a*s,e},B.calculateW=function(e,t){var n=t[0],r=t[1],i=t[2];return e[0]=n,e[1]=r,e[2]=i,e[3]=Math.sqrt(Math.abs(1-n*n-r*r-i*i)),e},B.dot=R.dot,B.lerp=R.lerp,B.slerp=function(e,t,n,r){var i=t[0],a=t[1],o=t[2],s=t[3],c=n[0],l=n[1],u=n[2],d=n[3],f,p=i*c+a*l+o*u+s*d,m,h,g;return p<0&&(p=-p,c=-c,l=-l,u=-u,d=-d),1-p>1e-6?(f=Math.acos(p),m=Math.sin(f),h=Math.sin((1-r)*f)/m,g=Math.sin(r*f)/m):(h=1-r,g=r),e[0]=h*i+g*c,e[1]=h*a+g*l,e[2]=h*o+g*u,e[3]=h*s+g*d,e},B.invert=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=n*n+r*r+i*i+a*a,s=o?1/o:0;return e[0]=-n*s,e[1]=-r*s,e[2]=-i*s,e[3]=a*s,e},B.conjugate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e[2]=-t[2],e[3]=t[3],e},B.length=R.length,B.len=B.length,B.squaredLength=R.squaredLength,B.sqrLen=B.squaredLength,B.normalize=R.normalize,B.fromMat3=function(e,t){var n=t[0]+t[4]+t[8],r;if(n>0)r=Math.sqrt(n+1),e[3]=.5*r,r=.5/r,e[0]=(t[5]-t[7])*r,e[1]=(t[6]-t[2])*r,e[2]=(t[1]-t[3])*r;else{var i=0;t[4]>t[0]&&(i=1),t[8]>t[i*3+i]&&(i=2);var a=(i+1)%3,o=(i+2)%3;r=Math.sqrt(t[i*3+i]-t[a*3+a]-t[o*3+o]+1),e[i]=.5*r,r=.5/r,e[3]=(t[a*3+o]-t[o*3+a])*r,e[a]=(t[a*3+i]+t[i*3+a])*r,e[o]=(t[o*3+i]+t[i*3+o])*r}return e};var We=function(e,t,n,r){e=e||0,t=t||0,n=n||0,r=r===void 0?1:r,this.array=B.fromValues(e,t,n,r),this._dirty=!0};We.prototype={constructor:We,add:function(e){return B.add(this.array,this.array,e.array),this._dirty=!0,this},calculateW:function(){return B.calculateW(this.array,this.array),this._dirty=!0,this},set:function(e,t,n,r){return this.array[0]=e,this.array[1]=t,this.array[2]=n,this.array[3]=r,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this.array[2]=e[2],this.array[3]=e[3],this._dirty=!0,this},clone:function(){return new We(this.x,this.y,this.z,this.w)},conjugate:function(){return B.conjugate(this.array,this.array),this._dirty=!0,this},copy:function(e){return B.copy(this.array,e.array),this._dirty=!0,this},dot:function(e){return B.dot(this.array,e.array)},fromMat3:function(e){return B.fromMat3(this.array,e.array),this._dirty=!0,this},fromMat4:(function(){var e=z.create();return function(t){return z.fromMat4(e,t.array),z.transpose(e,e),B.fromMat3(this.array,e),this._dirty=!0,this}})(),identity:function(){return B.identity(this.array),this._dirty=!0,this},invert:function(){return B.invert(this.array,this.array),this._dirty=!0,this},len:function(){return B.len(this.array)},length:function(){return B.length(this.array)},lerp:function(e,t,n){return B.lerp(this.array,e.array,t.array,n),this._dirty=!0,this},mul:function(e){return B.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return B.multiply(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return B.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return B.multiply(this.array,e.array,this.array),this._dirty=!0,this},normalize:function(){return B.normalize(this.array,this.array),this._dirty=!0,this},rotateX:function(e){return B.rotateX(this.array,this.array,e),this._dirty=!0,this},rotateY:function(e){return B.rotateY(this.array,this.array,e),this._dirty=!0,this},rotateZ:function(e){return B.rotateZ(this.array,this.array,e),this._dirty=!0,this},rotationTo:function(e,t){return B.rotationTo(this.array,e.array,t.array),this._dirty=!0,this},setAxes:function(e,t,n){return B.setAxes(this.array,e.array,t.array,n.array),this._dirty=!0,this},setAxisAngle:function(e,t){return B.setAxisAngle(this.array,e.array,t),this._dirty=!0,this},slerp:function(e,t,n){return B.slerp(this.array,e.array,t.array,n),this._dirty=!0,this},sqrLen:function(){return B.sqrLen(this.array)},squaredLength:function(){return B.squaredLength(this.array)},fromEuler:function(e,t){return We.fromEuler(this,e,t)},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}};var Ge=Object.defineProperty;if(Ge){var Ke=We.prototype;Ge(Ke,`x`,{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),Ge(Ke,`y`,{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}}),Ge(Ke,`z`,{get:function(){return this.array[2]},set:function(e){this.array[2]=e,this._dirty=!0}}),Ge(Ke,`w`,{get:function(){return this.array[3]},set:function(e){this.array[3]=e,this._dirty=!0}})}We.add=function(e,t,n){return B.add(e.array,t.array,n.array),e._dirty=!0,e},We.set=function(e,t,n,r,i){B.set(e.array,t,n,r,i),e._dirty=!0},We.copy=function(e,t){return B.copy(e.array,t.array),e._dirty=!0,e},We.calculateW=function(e,t){return B.calculateW(e.array,t.array),e._dirty=!0,e},We.conjugate=function(e,t){return B.conjugate(e.array,t.array),e._dirty=!0,e},We.identity=function(e){return B.identity(e.array),e._dirty=!0,e},We.invert=function(e,t){return B.invert(e.array,t.array),e._dirty=!0,e},We.dot=function(e,t){return B.dot(e.array,t.array)},We.len=function(e){return B.length(e.array)},We.lerp=function(e,t,n,r){return B.lerp(e.array,t.array,n.array,r),e._dirty=!0,e},We.slerp=function(e,t,n,r){return B.slerp(e.array,t.array,n.array,r),e._dirty=!0,e},We.mul=function(e,t,n){return B.multiply(e.array,t.array,n.array),e._dirty=!0,e},We.multiply=We.mul,We.rotateX=function(e,t,n){return B.rotateX(e.array,t.array,n),e._dirty=!0,e},We.rotateY=function(e,t,n){return B.rotateY(e.array,t.array,n),e._dirty=!0,e},We.rotateZ=function(e,t,n){return B.rotateZ(e.array,t.array,n),e._dirty=!0,e},We.setAxisAngle=function(e,t,n){return B.setAxisAngle(e.array,t.array,n),e._dirty=!0,e},We.normalize=function(e,t){return B.normalize(e.array,t.array),e._dirty=!0,e},We.sqrLen=function(e){return B.sqrLen(e.array)},We.squaredLength=We.sqrLen,We.fromMat3=function(e,t){return B.fromMat3(e.array,t.array),e._dirty=!0,e},We.setAxes=function(e,t,n,r){return B.setAxes(e.array,t.array,n.array,r.array),e._dirty=!0,e},We.rotationTo=function(e,t,n){return B.rotationTo(e.array,t.array,n.array),e._dirty=!0,e},We.fromEuler=function(e,t,n){e._dirty=!0,t=t.array;var r=e.array,i=Math.cos(t[0]/2),a=Math.cos(t[1]/2),o=Math.cos(t[2]/2),s=Math.sin(t[0]/2),c=Math.sin(t[1]/2),l=Math.sin(t[2]/2),n=(n||`XYZ`).toUpperCase();switch(n){case`XYZ`:r[0]=s*a*o+i*c*l,r[1]=i*c*o-s*a*l,r[2]=i*a*l+s*c*o,r[3]=i*a*o-s*c*l;break;case`YXZ`:r[0]=s*a*o+i*c*l,r[1]=i*c*o-s*a*l,r[2]=i*a*l-s*c*o,r[3]=i*a*o+s*c*l;break;case`ZXY`:r[0]=s*a*o-i*c*l,r[1]=i*c*o+s*a*l,r[2]=i*a*l+s*c*o,r[3]=i*a*o-s*c*l;break;case`ZYX`:r[0]=s*a*o-i*c*l,r[1]=i*c*o+s*a*l,r[2]=i*a*l-s*c*o,r[3]=i*a*o+s*c*l;break;case`YZX`:r[0]=s*a*o+i*c*l,r[1]=i*c*o+s*a*l,r[2]=i*a*l-s*c*o,r[3]=i*a*o-s*c*l;break;case`XZY`:r[0]=s*a*o-i*c*l,r[1]=i*c*o-s*a*l,r[2]=i*a*l+s*c*o,r[3]=i*a*o+s*c*l;break}};var V={};V.create=function(){var e=new Ie(16);return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=1,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=1,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,e},V.clone=function(e){var t=new Ie(16);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t[4]=e[4],t[5]=e[5],t[6]=e[6],t[7]=e[7],t[8]=e[8],t[9]=e[9],t[10]=e[10],t[11]=e[11],t[12]=e[12],t[13]=e[13],t[14]=e[14],t[15]=e[15],t},V.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e[6]=t[6],e[7]=t[7],e[8]=t[8],e[9]=t[9],e[10]=t[10],e[11]=t[11],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15],e},V.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=1,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=1,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,e},V.transpose=function(e,t){if(e===t){var n=t[1],r=t[2],i=t[3],a=t[6],o=t[7],s=t[11];e[1]=t[4],e[2]=t[8],e[3]=t[12],e[4]=n,e[6]=t[9],e[7]=t[13],e[8]=r,e[9]=a,e[11]=t[14],e[12]=i,e[13]=o,e[14]=s}else e[0]=t[0],e[1]=t[4],e[2]=t[8],e[3]=t[12],e[4]=t[1],e[5]=t[5],e[6]=t[9],e[7]=t[13],e[8]=t[2],e[9]=t[6],e[10]=t[10],e[11]=t[14],e[12]=t[3],e[13]=t[7],e[14]=t[11],e[15]=t[15];return e},V.invert=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=t[4],s=t[5],c=t[6],l=t[7],u=t[8],d=t[9],f=t[10],p=t[11],m=t[12],h=t[13],g=t[14],_=t[15],v=n*s-r*o,y=n*c-i*o,b=n*l-a*o,x=r*c-i*s,S=r*l-a*s,C=i*l-a*c,w=u*h-d*m,T=u*g-f*m,E=u*_-p*m,D=d*g-f*h,O=d*_-p*h,k=f*_-p*g,A=v*k-y*O+b*D+x*E-S*T+C*w;return A?(A=1/A,e[0]=(s*k-c*O+l*D)*A,e[1]=(i*O-r*k-a*D)*A,e[2]=(h*C-g*S+_*x)*A,e[3]=(f*S-d*C-p*x)*A,e[4]=(c*E-o*k-l*T)*A,e[5]=(n*k-i*E+a*T)*A,e[6]=(g*b-m*C-_*y)*A,e[7]=(u*C-f*b+p*y)*A,e[8]=(o*O-s*E+l*w)*A,e[9]=(r*E-n*O-a*w)*A,e[10]=(m*S-h*b+_*v)*A,e[11]=(d*b-u*S-p*v)*A,e[12]=(s*T-o*D-c*w)*A,e[13]=(n*D-r*T+i*w)*A,e[14]=(h*y-m*x-g*v)*A,e[15]=(u*x-d*y+f*v)*A,e):null},V.adjoint=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=t[4],s=t[5],c=t[6],l=t[7],u=t[8],d=t[9],f=t[10],p=t[11],m=t[12],h=t[13],g=t[14],_=t[15];return e[0]=s*(f*_-p*g)-d*(c*_-l*g)+h*(c*p-l*f),e[1]=-(r*(f*_-p*g)-d*(i*_-a*g)+h*(i*p-a*f)),e[2]=r*(c*_-l*g)-s*(i*_-a*g)+h*(i*l-a*c),e[3]=-(r*(c*p-l*f)-s*(i*p-a*f)+d*(i*l-a*c)),e[4]=-(o*(f*_-p*g)-u*(c*_-l*g)+m*(c*p-l*f)),e[5]=n*(f*_-p*g)-u*(i*_-a*g)+m*(i*p-a*f),e[6]=-(n*(c*_-l*g)-o*(i*_-a*g)+m*(i*l-a*c)),e[7]=n*(c*p-l*f)-o*(i*p-a*f)+u*(i*l-a*c),e[8]=o*(d*_-p*h)-u*(s*_-l*h)+m*(s*p-l*d),e[9]=-(n*(d*_-p*h)-u*(r*_-a*h)+m*(r*p-a*d)),e[10]=n*(s*_-l*h)-o*(r*_-a*h)+m*(r*l-a*s),e[11]=-(n*(s*p-l*d)-o*(r*p-a*d)+u*(r*l-a*s)),e[12]=-(o*(d*g-f*h)-u*(s*g-c*h)+m*(s*f-c*d)),e[13]=n*(d*g-f*h)-u*(r*g-i*h)+m*(r*f-i*d),e[14]=-(n*(s*g-c*h)-o*(r*g-i*h)+m*(r*c-i*s)),e[15]=n*(s*f-c*d)-o*(r*f-i*d)+u*(r*c-i*s),e},V.determinant=function(e){var t=e[0],n=e[1],r=e[2],i=e[3],a=e[4],o=e[5],s=e[6],c=e[7],l=e[8],u=e[9],d=e[10],f=e[11],p=e[12],m=e[13],h=e[14],g=e[15],_=t*o-n*a,v=t*s-r*a,y=t*c-i*a,b=n*s-r*o,x=n*c-i*o,S=r*c-i*s,C=l*m-u*p,w=l*h-d*p,T=l*g-f*p,E=u*h-d*m,D=u*g-f*m;return _*(d*g-f*h)-v*D+y*E+b*T-x*w+S*C},V.multiply=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=t[6],u=t[7],d=t[8],f=t[9],p=t[10],m=t[11],h=t[12],g=t[13],_=t[14],v=t[15],y=n[0],b=n[1],x=n[2],S=n[3];return e[0]=y*r+b*s+x*d+S*h,e[1]=y*i+b*c+x*f+S*g,e[2]=y*a+b*l+x*p+S*_,e[3]=y*o+b*u+x*m+S*v,y=n[4],b=n[5],x=n[6],S=n[7],e[4]=y*r+b*s+x*d+S*h,e[5]=y*i+b*c+x*f+S*g,e[6]=y*a+b*l+x*p+S*_,e[7]=y*o+b*u+x*m+S*v,y=n[8],b=n[9],x=n[10],S=n[11],e[8]=y*r+b*s+x*d+S*h,e[9]=y*i+b*c+x*f+S*g,e[10]=y*a+b*l+x*p+S*_,e[11]=y*o+b*u+x*m+S*v,y=n[12],b=n[13],x=n[14],S=n[15],e[12]=y*r+b*s+x*d+S*h,e[13]=y*i+b*c+x*f+S*g,e[14]=y*a+b*l+x*p+S*_,e[15]=y*o+b*u+x*m+S*v,e},V.multiplyAffine=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[4],s=t[5],c=t[6],l=t[8],u=t[9],d=t[10],f=t[12],p=t[13],m=t[14],h=n[0],g=n[1],_=n[2];return e[0]=h*r+g*o+_*l,e[1]=h*i+g*s+_*u,e[2]=h*a+g*c+_*d,h=n[4],g=n[5],_=n[6],e[4]=h*r+g*o+_*l,e[5]=h*i+g*s+_*u,e[6]=h*a+g*c+_*d,h=n[8],g=n[9],_=n[10],e[8]=h*r+g*o+_*l,e[9]=h*i+g*s+_*u,e[10]=h*a+g*c+_*d,h=n[12],g=n[13],_=n[14],e[12]=h*r+g*o+_*l+f,e[13]=h*i+g*s+_*u+p,e[14]=h*a+g*c+_*d+m,e},V.mul=V.multiply,V.mulAffine=V.multiplyAffine,V.translate=function(e,t,n){var r=n[0],i=n[1],a=n[2],o,s,c,l,u,d,f,p,m,h,g,_;return t===e?(e[12]=t[0]*r+t[4]*i+t[8]*a+t[12],e[13]=t[1]*r+t[5]*i+t[9]*a+t[13],e[14]=t[2]*r+t[6]*i+t[10]*a+t[14],e[15]=t[3]*r+t[7]*i+t[11]*a+t[15]):(o=t[0],s=t[1],c=t[2],l=t[3],u=t[4],d=t[5],f=t[6],p=t[7],m=t[8],h=t[9],g=t[10],_=t[11],e[0]=o,e[1]=s,e[2]=c,e[3]=l,e[4]=u,e[5]=d,e[6]=f,e[7]=p,e[8]=m,e[9]=h,e[10]=g,e[11]=_,e[12]=o*r+u*i+m*a+t[12],e[13]=s*r+d*i+h*a+t[13],e[14]=c*r+f*i+g*a+t[14],e[15]=l*r+p*i+_*a+t[15]),e},V.scale=function(e,t,n){var r=n[0],i=n[1],a=n[2];return e[0]=t[0]*r,e[1]=t[1]*r,e[2]=t[2]*r,e[3]=t[3]*r,e[4]=t[4]*i,e[5]=t[5]*i,e[6]=t[6]*i,e[7]=t[7]*i,e[8]=t[8]*a,e[9]=t[9]*a,e[10]=t[10]*a,e[11]=t[11]*a,e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15],e},V.rotate=function(e,t,n,r){var i=r[0],a=r[1],o=r[2],s=Math.sqrt(i*i+a*a+o*o),c,l,u,d,f,p,m,h,g,_,v,y,b,x,S,C,w,T,E,D,O,k,A,j;return Math.abs(s)<1e-6?null:(s=1/s,i*=s,a*=s,o*=s,c=Math.sin(n),l=Math.cos(n),u=1-l,d=t[0],f=t[1],p=t[2],m=t[3],h=t[4],g=t[5],_=t[6],v=t[7],y=t[8],b=t[9],x=t[10],S=t[11],C=i*i*u+l,w=a*i*u+o*c,T=o*i*u-a*c,E=i*a*u-o*c,D=a*a*u+l,O=o*a*u+i*c,k=i*o*u+a*c,A=a*o*u-i*c,j=o*o*u+l,e[0]=d*C+h*w+y*T,e[1]=f*C+g*w+b*T,e[2]=p*C+_*w+x*T,e[3]=m*C+v*w+S*T,e[4]=d*E+h*D+y*O,e[5]=f*E+g*D+b*O,e[6]=p*E+_*D+x*O,e[7]=m*E+v*D+S*O,e[8]=d*k+h*A+y*j,e[9]=f*k+g*A+b*j,e[10]=p*k+_*A+x*j,e[11]=m*k+v*A+S*j,t!==e&&(e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e)},V.rotateX=function(e,t,n){var r=Math.sin(n),i=Math.cos(n),a=t[4],o=t[5],s=t[6],c=t[7],l=t[8],u=t[9],d=t[10],f=t[11];return t!==e&&(e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e[4]=a*i+l*r,e[5]=o*i+u*r,e[6]=s*i+d*r,e[7]=c*i+f*r,e[8]=l*i-a*r,e[9]=u*i-o*r,e[10]=d*i-s*r,e[11]=f*i-c*r,e},V.rotateY=function(e,t,n){var r=Math.sin(n),i=Math.cos(n),a=t[0],o=t[1],s=t[2],c=t[3],l=t[8],u=t[9],d=t[10],f=t[11];return t!==e&&(e[4]=t[4],e[5]=t[5],e[6]=t[6],e[7]=t[7],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e[0]=a*i-l*r,e[1]=o*i-u*r,e[2]=s*i-d*r,e[3]=c*i-f*r,e[8]=a*r+l*i,e[9]=o*r+u*i,e[10]=s*r+d*i,e[11]=c*r+f*i,e},V.rotateZ=function(e,t,n){var r=Math.sin(n),i=Math.cos(n),a=t[0],o=t[1],s=t[2],c=t[3],l=t[4],u=t[5],d=t[6],f=t[7];return t!==e&&(e[8]=t[8],e[9]=t[9],e[10]=t[10],e[11]=t[11],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e[0]=a*i+l*r,e[1]=o*i+u*r,e[2]=s*i+d*r,e[3]=c*i+f*r,e[4]=l*i-a*r,e[5]=u*i-o*r,e[6]=d*i-s*r,e[7]=f*i-c*r,e},V.fromRotationTranslation=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=r+r,c=i+i,l=a+a,u=r*s,d=r*c,f=r*l,p=i*c,m=i*l,h=a*l,g=o*s,_=o*c,v=o*l;return e[0]=1-(p+h),e[1]=d+v,e[2]=f-_,e[3]=0,e[4]=d-v,e[5]=1-(u+h),e[6]=m+g,e[7]=0,e[8]=f+_,e[9]=m-g,e[10]=1-(u+p),e[11]=0,e[12]=n[0],e[13]=n[1],e[14]=n[2],e[15]=1,e},V.fromQuat=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=n+n,s=r+r,c=i+i,l=n*o,u=r*o,d=r*s,f=i*o,p=i*s,m=i*c,h=a*o,g=a*s,_=a*c;return e[0]=1-d-m,e[1]=u+_,e[2]=f-g,e[3]=0,e[4]=u-_,e[5]=1-l-m,e[6]=p+h,e[7]=0,e[8]=f+g,e[9]=p-h,e[10]=1-l-d,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,e},V.frustum=function(e,t,n,r,i,a,o){var s=1/(n-t),c=1/(i-r),l=1/(a-o);return e[0]=a*2*s,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=a*2*c,e[6]=0,e[7]=0,e[8]=(n+t)*s,e[9]=(i+r)*c,e[10]=(o+a)*l,e[11]=-1,e[12]=0,e[13]=0,e[14]=o*a*2*l,e[15]=0,e},V.perspective=function(e,t,n,r,i){var a=1/Math.tan(t/2),o=1/(r-i);return e[0]=a/n,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=a,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=(i+r)*o,e[11]=-1,e[12]=0,e[13]=0,e[14]=2*i*r*o,e[15]=0,e},V.ortho=function(e,t,n,r,i,a,o){var s=1/(t-n),c=1/(r-i),l=1/(a-o);return e[0]=-2*s,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=-2*c,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=2*l,e[11]=0,e[12]=(t+n)*s,e[13]=(i+r)*c,e[14]=(o+a)*l,e[15]=1,e},V.lookAt=function(e,t,n,r){var i,a,o,s,c,l,u,d,f,p,m=t[0],h=t[1],g=t[2],_=r[0],v=r[1],y=r[2],b=n[0],x=n[1],S=n[2];return Math.abs(m-b)<1e-6&&Math.abs(h-x)<1e-6&&Math.abs(g-S)<1e-6?V.identity(e):(u=m-b,d=h-x,f=g-S,p=1/Math.sqrt(u*u+d*d+f*f),u*=p,d*=p,f*=p,i=v*f-y*d,a=y*u-_*f,o=_*d-v*u,p=Math.sqrt(i*i+a*a+o*o),p?(p=1/p,i*=p,a*=p,o*=p):(i=0,a=0,o=0),s=d*o-f*a,c=f*i-u*o,l=u*a-d*i,p=Math.sqrt(s*s+c*c+l*l),p?(p=1/p,s*=p,c*=p,l*=p):(s=0,c=0,l=0),e[0]=i,e[1]=s,e[2]=u,e[3]=0,e[4]=a,e[5]=c,e[6]=d,e[7]=0,e[8]=o,e[9]=l,e[10]=f,e[11]=0,e[12]=-(i*m+a*h+o*g),e[13]=-(s*m+c*h+l*g),e[14]=-(u*m+d*h+f*g),e[15]=1,e)},V.frob=function(e){return Math.sqrt(e[0]**2+e[1]**2+e[2]**2+e[3]**2+e[4]**2+e[5]**2+e[6]**2+e[7]**2+e[8]**2+e[9]**2+e[10]**2+e[11]**2+e[12]**2+e[13]**2+e[14]**2+e[15]**2)};var H=function(){this._axisX=new L,this._axisY=new L,this._axisZ=new L,this.array=V.create(),this._dirty=!0};H.prototype={constructor:H,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},adjoint:function(){return V.adjoint(this.array,this.array),this._dirty=!0,this},clone:function(){return new H().copy(this)},copy:function(e){return V.copy(this.array,e.array),this._dirty=!0,this},determinant:function(){return V.determinant(this.array)},fromQuat:function(e){return V.fromQuat(this.array,e.array),this._dirty=!0,this},fromRotationTranslation:function(e,t){return V.fromRotationTranslation(this.array,e.array,t.array),this._dirty=!0,this},fromMat2d:function(e){return H.fromMat2d(this,e),this},frustum:function(e,t,n,r,i,a){return V.frustum(this.array,e,t,n,r,i,a),this._dirty=!0,this},identity:function(){return V.identity(this.array),this._dirty=!0,this},invert:function(){return V.invert(this.array,this.array),this._dirty=!0,this},lookAt:function(e,t,n){return V.lookAt(this.array,e.array,t.array,n.array),this._dirty=!0,this},mul:function(e){return V.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return V.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return V.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return V.multiply(this.array,e.array,this.array),this._dirty=!0,this},ortho:function(e,t,n,r,i,a){return V.ortho(this.array,e,t,n,r,i,a),this._dirty=!0,this},perspective:function(e,t,n,r){return V.perspective(this.array,e,t,n,r),this._dirty=!0,this},rotate:function(e,t){return V.rotate(this.array,this.array,e,t.array),this._dirty=!0,this},rotateX:function(e){return V.rotateX(this.array,this.array,e),this._dirty=!0,this},rotateY:function(e){return V.rotateY(this.array,this.array,e),this._dirty=!0,this},rotateZ:function(e){return V.rotateZ(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return V.scale(this.array,this.array,e.array),this._dirty=!0,this},translate:function(e){return V.translate(this.array,this.array,e.array),this._dirty=!0,this},transpose:function(){return V.transpose(this.array,this.array),this._dirty=!0,this},decomposeMatrix:(function(){var e=I.create(),t=I.create(),n=I.create(),r=z.create();return function(i,a,o){var s=this.array;I.set(e,s[0],s[1],s[2]),I.set(t,s[4],s[5],s[6]),I.set(n,s[8],s[9],s[10]);var c=I.length(e),l=I.length(t),u=I.length(n);this.determinant()<0&&(c=-c),i&&i.set(c,l,u),o.set(s[12],s[13],s[14]),z.fromMat4(r,s),r[0]/=c,r[1]/=c,r[2]/=c,r[3]/=l,r[4]/=l,r[5]/=l,r[6]/=u,r[7]/=u,r[8]/=u,B.fromMat3(a.array,r),B.normalize(a.array,a.array),a._dirty=!0,o._dirty=!0}})(),toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}};var qe=Object.defineProperty;if(qe){var Je=H.prototype;qe(Je,`z`,{get:function(){var e=this.array;return this._axisZ.set(e[8],e[9],e[10]),this._axisZ},set:function(e){var t=this.array;e=e.array,t[8]=e[0],t[9]=e[1],t[10]=e[2],this._dirty=!0}}),qe(Je,`y`,{get:function(){var e=this.array;return this._axisY.set(e[4],e[5],e[6]),this._axisY},set:function(e){var t=this.array;e=e.array,t[4]=e[0],t[5]=e[1],t[6]=e[2],this._dirty=!0}}),qe(Je,`x`,{get:function(){var e=this.array;return this._axisX.set(e[0],e[1],e[2]),this._axisX},set:function(e){var t=this.array;e=e.array,t[0]=e[0],t[1]=e[1],t[2]=e[2],this._dirty=!0}})}H.adjoint=function(e,t){return V.adjoint(e.array,t.array),e._dirty=!0,e},H.copy=function(e,t){return V.copy(e.array,t.array),e._dirty=!0,e},H.determinant=function(e){return V.determinant(e.array)},H.identity=function(e){return V.identity(e.array),e._dirty=!0,e},H.ortho=function(e,t,n,r,i,a,o){return V.ortho(e.array,t,n,r,i,a,o),e._dirty=!0,e},H.perspective=function(e,t,n,r,i){return V.perspective(e.array,t,n,r,i),e._dirty=!0,e},H.lookAt=function(e,t,n,r){return V.lookAt(e.array,t.array,n.array,r.array),e._dirty=!0,e},H.invert=function(e,t){return V.invert(e.array,t.array),e._dirty=!0,e},H.mul=function(e,t,n){return V.mul(e.array,t.array,n.array),e._dirty=!0,e},H.multiply=H.mul,H.fromQuat=function(e,t){return V.fromQuat(e.array,t.array),e._dirty=!0,e},H.fromRotationTranslation=function(e,t,n){return V.fromRotationTranslation(e.array,t.array,n.array),e._dirty=!0,e},H.fromMat2d=function(e,t){e._dirty=!0;var t=t.array,e=e.array;return e[0]=t[0],e[4]=t[2],e[12]=t[4],e[1]=t[1],e[5]=t[3],e[13]=t[5],e},H.rotate=function(e,t,n,r){return V.rotate(e.array,t.array,n,r.array),e._dirty=!0,e},H.rotateX=function(e,t,n){return V.rotateX(e.array,t.array,n),e._dirty=!0,e},H.rotateY=function(e,t,n){return V.rotateY(e.array,t.array,n),e._dirty=!0,e},H.rotateZ=function(e,t,n){return V.rotateZ(e.array,t.array,n),e._dirty=!0,e},H.scale=function(e,t,n){return V.scale(e.array,t.array,n.array),e._dirty=!0,e},H.transpose=function(e,t){return V.transpose(e.array,t.array),e._dirty=!0,e},H.translate=function(e,t,n){return V.translate(e.array,t.array,n.array),e._dirty=!0,e};var Ye=I.set,Xe=I.copy,Ze=function(e,t){this.min=e||new L(1/0,1/0,1/0),this.max=t||new L(-1/0,-1/0,-1/0),this.vertices=null};Ze.prototype={constructor:Ze,updateFromVertices:function(e){if(e.length>0){var t=this.min,n=this.max,r=t.array,i=n.array;Xe(r,e[0]),Xe(i,e[0]);for(var a=1;a<e.length;a++){var o=e[a];o[0]<r[0]&&(r[0]=o[0]),o[1]<r[1]&&(r[1]=o[1]),o[2]<r[2]&&(r[2]=o[2]),o[0]>i[0]&&(i[0]=o[0]),o[1]>i[1]&&(i[1]=o[1]),o[2]>i[2]&&(i[2]=o[2])}t._dirty=!0,n._dirty=!0}},union:function(e){var t=this.min,n=this.max;return I.min(t.array,t.array,e.min.array),I.max(n.array,n.array,e.max.array),t._dirty=!0,n._dirty=!0,this},intersection:function(e){var t=this.min,n=this.max;return I.max(t.array,t.array,e.min.array),I.min(n.array,n.array,e.max.array),t._dirty=!0,n._dirty=!0,this},intersectBoundingBox:function(e){var t=this.min.array,n=this.max.array,r=e.min.array,i=e.max.array;return!(t[0]>i[0]||t[1]>i[1]||t[2]>i[2]||n[0]<r[0]||n[1]<r[1]||n[2]<r[2])},containBoundingBox:function(e){var t=this.min.array,n=this.max.array,r=e.min.array,i=e.max.array;return t[0]<=r[0]&&t[1]<=r[1]&&t[2]<=r[2]&&n[0]>=i[0]&&n[1]>=i[1]&&n[2]>=i[2]},containPoint:function(e){var t=this.min.array,n=this.max.array,r=e.array;return t[0]<=r[0]&&t[1]<=r[1]&&t[2]<=r[2]&&n[0]>=r[0]&&n[1]>=r[1]&&n[2]>=r[2]},isFinite:function(){var e=this.min.array,t=this.max.array;return isFinite(e[0])&&isFinite(e[1])&&isFinite(e[2])&&isFinite(t[0])&&isFinite(t[1])&&isFinite(t[2])},applyTransform:function(e){this.transformFrom(this,e)},transformFrom:(function(){var e=I.create(),t=I.create(),n=I.create(),r=I.create(),i=I.create(),a=I.create();return function(o,s){var c=o.min.array,l=o.max.array,u=s.array;return e[0]=u[0]*c[0],e[1]=u[1]*c[0],e[2]=u[2]*c[0],t[0]=u[0]*l[0],t[1]=u[1]*l[0],t[2]=u[2]*l[0],n[0]=u[4]*c[1],n[1]=u[5]*c[1],n[2]=u[6]*c[1],r[0]=u[4]*l[1],r[1]=u[5]*l[1],r[2]=u[6]*l[1],i[0]=u[8]*c[2],i[1]=u[9]*c[2],i[2]=u[10]*c[2],a[0]=u[8]*l[2],a[1]=u[9]*l[2],a[2]=u[10]*l[2],c=this.min.array,l=this.max.array,c[0]=Math.min(e[0],t[0])+Math.min(n[0],r[0])+Math.min(i[0],a[0])+u[12],c[1]=Math.min(e[1],t[1])+Math.min(n[1],r[1])+Math.min(i[1],a[1])+u[13],c[2]=Math.min(e[2],t[2])+Math.min(n[2],r[2])+Math.min(i[2],a[2])+u[14],l[0]=Math.max(e[0],t[0])+Math.max(n[0],r[0])+Math.max(i[0],a[0])+u[12],l[1]=Math.max(e[1],t[1])+Math.max(n[1],r[1])+Math.max(i[1],a[1])+u[13],l[2]=Math.max(e[2],t[2])+Math.max(n[2],r[2])+Math.max(i[2],a[2])+u[14],this.min._dirty=!0,this.max._dirty=!0,this}})(),applyProjection:function(e){var t=this.min.array,n=this.max.array,r=e.array,i=t[0],a=t[1],o=t[2],s=n[0],c=n[1],l=t[2],u=n[0],d=n[1],f=n[2];if(r[15]===1)t[0]=r[0]*i+r[12],t[1]=r[5]*a+r[13],n[2]=r[10]*o+r[14],n[0]=r[0]*u+r[12],n[1]=r[5]*d+r[13],t[2]=r[10]*f+r[14];else{var p=-1/o;t[0]=r[0]*i*p,t[1]=r[5]*a*p,n[2]=(r[10]*o+r[14])*p,p=-1/l,n[0]=r[0]*s*p,n[1]=r[5]*c*p,p=-1/f,t[2]=(r[10]*f+r[14])*p}return this.min._dirty=!0,this.max._dirty=!0,this},updateVertices:function(){var e=this.vertices;if(!e){e=[];for(var t=0;t<8;t++)e[t]=I.fromValues(0,0,0);this.vertices=e}var n=this.min.array,r=this.max.array;return Ye(e[0],n[0],n[1],n[2]),Ye(e[1],n[0],r[1],n[2]),Ye(e[2],r[0],n[1],n[2]),Ye(e[3],r[0],r[1],n[2]),Ye(e[4],n[0],n[1],r[2]),Ye(e[5],n[0],r[1],r[2]),Ye(e[6],r[0],n[1],r[2]),Ye(e[7],r[0],r[1],r[2]),this},copy:function(e){var t=this.min,n=this.max;return Xe(t.array,e.min.array),Xe(n.array,e.max.array),t._dirty=!0,n._dirty=!0,this},clone:function(){var e=new Ze;return e.copy(this),e}};var Qe=0,$e=Fe.extend({name:``,position:null,rotation:null,scale:null,worldTransform:null,localTransform:null,autoUpdateLocalTransform:!0,_parent:null,_scene:null,_needsUpdateWorldTransform:!0,_inIterating:!1,__depth:0},function(){this.name||(this.name=(this.type||`NODE`)+`_`+Qe++),this.position||(this.position=new L),this.rotation||(this.rotation=new We),this.scale||(this.scale=new L(1,1,1)),this.worldTransform=new H,this.localTransform=new H,this._children=[]},{target:null,invisible:!1,isSkinnedMesh:function(){return!1},isRenderable:function(){return!1},setName:function(e){var t=this._scene;if(t){var n=t._nodeRepository;delete n[this.name],n[e]=this}this.name=e},add:function(e){var t=e._parent;if(t!==this){t&&t.remove(e),e._parent=this,this._children.push(e);var n=this._scene;n&&n!==e.scene&&e.traverse(this._addSelfToScene,this),e._needsUpdateWorldTransform=!0}},remove:function(e){var t=this._children,n=t.indexOf(e);n<0||(t.splice(n,1),e._parent=null,this._scene&&e.traverse(this._removeSelfFromScene,this))},removeAll:function(){for(var e=this._children,t=0;t<e.length;t++)e[t]._parent=null,this._scene&&e[t].traverse(this._removeSelfFromScene,this);this._children=[]},getScene:function(){return this._scene},getParent:function(){return this._parent},_removeSelfFromScene:function(e){e._scene.removeFromScene(e),e._scene=null},_addSelfToScene:function(e){this._scene.addToScene(e),e._scene=this._scene},isAncestor:function(e){for(var t=e._parent;t;){if(t===this)return!0;t=t._parent}return!1},children:function(){return this._children.slice()},childAt:function(e){return this._children[e]},getChildByName:function(e){for(var t=this._children,n=0;n<t.length;n++)if(t[n].name===e)return t[n]},getDescendantByName:function(e){for(var t=this._children,n=0;n<t.length;n++){var r=t[n];if(r.name===e)return r;var i=r.getDescendantByName(e);if(i)return i}},queryNode:function(e){if(e){for(var t=e.split(`/`),n=this,r=0;r<t.length;r++){var i=t[r];if(i){for(var a=!1,o=n._children,s=0;s<o.length;s++){var c=o[s];if(c.name===i){n=c,a=!0;break}}if(!a)return}}return n}},getPath:function(e){if(!this._parent)return`/`;for(var t=this._parent,n=this.name;t._parent&&(n=t.name+`/`+n,t._parent!=e);)t=t._parent;return!t._parent&&e?null:n},traverse:function(e,t){e.call(t,this);for(var n=this._children,r=0,i=n.length;r<i;r++)n[r].traverse(e,t)},eachChild:function(e,t){for(var n=this._children,r=0,i=n.length;r<i;r++){var a=n[r];e.call(t,a,r)}},setLocalTransform:function(e){V.copy(this.localTransform.array,e.array),this.decomposeLocalTransform()},decomposeLocalTransform:function(e){var t=e?null:this.scale;this.localTransform.decomposeMatrix(t,this.rotation,this.position)},setWorldTransform:function(e){V.copy(this.worldTransform.array,e.array),this.decomposeWorldTransform()},decomposeWorldTransform:(function(){var e=V.create();return function(t){var n=this.localTransform,r=this.worldTransform;this._parent?(V.invert(e,this._parent.worldTransform.array),V.multiply(n.array,e,r.array)):V.copy(n.array,r.array);var i=t?null:this.scale;n.decomposeMatrix(i,this.rotation,this.position)}})(),transformNeedsUpdate:function(){return this.position._dirty||this.rotation._dirty||this.scale._dirty},updateLocalTransform:function(){var e=this.position,t=this.rotation,n=this.scale;if(this.transformNeedsUpdate()){var r=this.localTransform.array;V.fromRotationTranslation(r,t.array,e.array),V.scale(r,r,n.array),t._dirty=!1,n._dirty=!1,e._dirty=!1,this._needsUpdateWorldTransform=!0}},_updateWorldTransformTopDown:function(){var e=this.localTransform.array,t=this.worldTransform.array;this._parent?V.multiplyAffine(t,this._parent.worldTransform.array,e):V.copy(t,e)},updateWorldTransform:function(){for(var e=this;e&&e.getParent()&&e.getParent().transformNeedsUpdate();)e=e.getParent();e.update()},update:function(e){this.autoUpdateLocalTransform?this.updateLocalTransform():e=!0,(e||this._needsUpdateWorldTransform)&&(this._updateWorldTransformTopDown(),e=!0,this._needsUpdateWorldTransform=!1);for(var t=this._children,n=0,r=t.length;n<r;n++)t[n].update(e)},getBoundingBox:(function(){function e(e){return!e.invisible&&e.geometry}var t=new Ze,n=new H,r=new H;return function(i,a){return a=a||new Ze,i=i||e,this._parent?H.invert(r,this._parent.worldTransform):H.identity(r),this.traverse(function(e){e.geometry&&e.geometry.boundingBox&&(t.copy(e.geometry.boundingBox),H.multiply(n,r,e.worldTransform),t.applyTransform(n),a.union(t))},this,e),a}})(),getWorldPosition:function(e){this.transformNeedsUpdate()&&this.updateWorldTransform();var t=this.worldTransform.array;if(e){var n=e.array;return n[0]=t[12],n[1]=t[13],n[2]=t[14],e}else return new L(t[12],t[13],t[14])},clone:function(){var e=new this.constructor,t=this._children;e.setName(this.name),e.position.copy(this.position),e.rotation.copy(this.rotation),e.scale.copy(this.scale);for(var n=0;n<t.length;n++)e.add(t[n].clone());return e},rotateAround:(function(){var e=new L,t=new H;return function(n,r,i){e.copy(this.position).subtract(n);var a=this.localTransform;a.identity(),a.translate(n),a.rotate(i,r),t.fromRotationTranslation(this.rotation,e),a.multiply(t),a.scale(this.scale),this.decomposeLocalTransform(),this._needsUpdateWorldTransform=!0}})(),lookAt:(function(){var e=new H;return function(t,n){e.lookAt(this.position,t,n||this.localTransform.y).invert(),this.setLocalTransform(e),this.target=t}})()}),U={DEPTH_BUFFER_BIT:256,STENCIL_BUFFER_BIT:1024,COLOR_BUFFER_BIT:16384,POINTS:0,LINES:1,LINE_LOOP:2,LINE_STRIP:3,TRIANGLES:4,TRIANGLE_STRIP:5,TRIANGLE_FAN:6,ZERO:0,ONE:1,SRC_COLOR:768,ONE_MINUS_SRC_COLOR:769,SRC_ALPHA:770,ONE_MINUS_SRC_ALPHA:771,DST_ALPHA:772,ONE_MINUS_DST_ALPHA:773,DST_COLOR:774,ONE_MINUS_DST_COLOR:775,SRC_ALPHA_SATURATE:776,FUNC_ADD:32774,BLEND_EQUATION:32777,BLEND_EQUATION_RGB:32777,BLEND_EQUATION_ALPHA:34877,FUNC_SUBTRACT:32778,FUNC_REVERSE_SUBTRACT:32779,BLEND_DST_RGB:32968,BLEND_SRC_RGB:32969,BLEND_DST_ALPHA:32970,BLEND_SRC_ALPHA:32971,CONSTANT_COLOR:32769,ONE_MINUS_CONSTANT_COLOR:32770,CONSTANT_ALPHA:32771,ONE_MINUS_CONSTANT_ALPHA:32772,BLEND_COLOR:32773,ARRAY_BUFFER:34962,ELEMENT_ARRAY_BUFFER:34963,ARRAY_BUFFER_BINDING:34964,ELEMENT_ARRAY_BUFFER_BINDING:34965,STREAM_DRAW:35040,STATIC_DRAW:35044,DYNAMIC_DRAW:35048,BUFFER_SIZE:34660,BUFFER_USAGE:34661,CURRENT_VERTEX_ATTRIB:34342,FRONT:1028,BACK:1029,FRONT_AND_BACK:1032,CULL_FACE:2884,BLEND:3042,DITHER:3024,STENCIL_TEST:2960,DEPTH_TEST:2929,SCISSOR_TEST:3089,POLYGON_OFFSET_FILL:32823,SAMPLE_ALPHA_TO_COVERAGE:32926,SAMPLE_COVERAGE:32928,NO_ERROR:0,INVALID_ENUM:1280,INVALID_VALUE:1281,INVALID_OPERATION:1282,OUT_OF_MEMORY:1285,CW:2304,CCW:2305,LINE_WIDTH:2849,ALIASED_POINT_SIZE_RANGE:33901,ALIASED_LINE_WIDTH_RANGE:33902,CULL_FACE_MODE:2885,FRONT_FACE:2886,DEPTH_RANGE:2928,DEPTH_WRITEMASK:2930,DEPTH_CLEAR_VALUE:2931,DEPTH_FUNC:2932,STENCIL_CLEAR_VALUE:2961,STENCIL_FUNC:2962,STENCIL_FAIL:2964,STENCIL_PASS_DEPTH_FAIL:2965,STENCIL_PASS_DEPTH_PASS:2966,STENCIL_REF:2967,STENCIL_VALUE_MASK:2963,STENCIL_WRITEMASK:2968,STENCIL_BACK_FUNC:34816,STENCIL_BACK_FAIL:34817,STENCIL_BACK_PASS_DEPTH_FAIL:34818,STENCIL_BACK_PASS_DEPTH_PASS:34819,STENCIL_BACK_REF:36003,STENCIL_BACK_VALUE_MASK:36004,STENCIL_BACK_WRITEMASK:36005,VIEWPORT:2978,SCISSOR_BOX:3088,COLOR_CLEAR_VALUE:3106,COLOR_WRITEMASK:3107,UNPACK_ALIGNMENT:3317,PACK_ALIGNMENT:3333,MAX_TEXTURE_SIZE:3379,MAX_VIEWPORT_DIMS:3386,SUBPIXEL_BITS:3408,RED_BITS:3410,GREEN_BITS:3411,BLUE_BITS:3412,ALPHA_BITS:3413,DEPTH_BITS:3414,STENCIL_BITS:3415,POLYGON_OFFSET_UNITS:10752,POLYGON_OFFSET_FACTOR:32824,TEXTURE_BINDING_2D:32873,SAMPLE_BUFFERS:32936,SAMPLES:32937,SAMPLE_COVERAGE_VALUE:32938,SAMPLE_COVERAGE_INVERT:32939,COMPRESSED_TEXTURE_FORMATS:34467,DONT_CARE:4352,FASTEST:4353,NICEST:4354,GENERATE_MIPMAP_HINT:33170,BYTE:5120,UNSIGNED_BYTE:5121,SHORT:5122,UNSIGNED_SHORT:5123,INT:5124,UNSIGNED_INT:5125,FLOAT:5126,DEPTH_COMPONENT:6402,ALPHA:6406,RGB:6407,RGBA:6408,LUMINANCE:6409,LUMINANCE_ALPHA:6410,UNSIGNED_SHORT_4_4_4_4:32819,UNSIGNED_SHORT_5_5_5_1:32820,UNSIGNED_SHORT_5_6_5:33635,FRAGMENT_SHADER:35632,VERTEX_SHADER:35633,MAX_VERTEX_ATTRIBS:34921,MAX_VERTEX_UNIFORM_VECTORS:36347,MAX_VARYING_VECTORS:36348,MAX_COMBINED_TEXTURE_IMAGE_UNITS:35661,MAX_VERTEX_TEXTURE_IMAGE_UNITS:35660,MAX_TEXTURE_IMAGE_UNITS:34930,MAX_FRAGMENT_UNIFORM_VECTORS:36349,SHADER_TYPE:35663,DELETE_STATUS:35712,LINK_STATUS:35714,VALIDATE_STATUS:35715,ATTACHED_SHADERS:35717,ACTIVE_UNIFORMS:35718,ACTIVE_ATTRIBUTES:35721,SHADING_LANGUAGE_VERSION:35724,CURRENT_PROGRAM:35725,NEVER:512,LESS:513,EQUAL:514,LEQUAL:515,GREATER:516,NOTEQUAL:517,GEQUAL:518,ALWAYS:519,KEEP:7680,REPLACE:7681,INCR:7682,DECR:7683,INVERT:5386,INCR_WRAP:34055,DECR_WRAP:34056,VENDOR:7936,RENDERER:7937,VERSION:7938,NEAREST:9728,LINEAR:9729,NEAREST_MIPMAP_NEAREST:9984,LINEAR_MIPMAP_NEAREST:9985,NEAREST_MIPMAP_LINEAR:9986,LINEAR_MIPMAP_LINEAR:9987,TEXTURE_MAG_FILTER:10240,TEXTURE_MIN_FILTER:10241,TEXTURE_WRAP_S:10242,TEXTURE_WRAP_T:10243,TEXTURE_2D:3553,TEXTURE:5890,TEXTURE_CUBE_MAP:34067,TEXTURE_BINDING_CUBE_MAP:34068,TEXTURE_CUBE_MAP_POSITIVE_X:34069,TEXTURE_CUBE_MAP_NEGATIVE_X:34070,TEXTURE_CUBE_MAP_POSITIVE_Y:34071,TEXTURE_CUBE_MAP_NEGATIVE_Y:34072,TEXTURE_CUBE_MAP_POSITIVE_Z:34073,TEXTURE_CUBE_MAP_NEGATIVE_Z:34074,MAX_CUBE_MAP_TEXTURE_SIZE:34076,TEXTURE0:33984,TEXTURE1:33985,TEXTURE2:33986,TEXTURE3:33987,TEXTURE4:33988,TEXTURE5:33989,TEXTURE6:33990,TEXTURE7:33991,TEXTURE8:33992,TEXTURE9:33993,TEXTURE10:33994,TEXTURE11:33995,TEXTURE12:33996,TEXTURE13:33997,TEXTURE14:33998,TEXTURE15:33999,TEXTURE16:34e3,TEXTURE17:34001,TEXTURE18:34002,TEXTURE19:34003,TEXTURE20:34004,TEXTURE21:34005,TEXTURE22:34006,TEXTURE23:34007,TEXTURE24:34008,TEXTURE25:34009,TEXTURE26:34010,TEXTURE27:34011,TEXTURE28:34012,TEXTURE29:34013,TEXTURE30:34014,TEXTURE31:34015,ACTIVE_TEXTURE:34016,REPEAT:10497,CLAMP_TO_EDGE:33071,MIRRORED_REPEAT:33648,FLOAT_VEC2:35664,FLOAT_VEC3:35665,FLOAT_VEC4:35666,INT_VEC2:35667,INT_VEC3:35668,INT_VEC4:35669,BOOL:35670,BOOL_VEC2:35671,BOOL_VEC3:35672,BOOL_VEC4:35673,FLOAT_MAT2:35674,FLOAT_MAT3:35675,FLOAT_MAT4:35676,SAMPLER_2D:35678,SAMPLER_CUBE:35680,VERTEX_ATTRIB_ARRAY_ENABLED:34338,VERTEX_ATTRIB_ARRAY_SIZE:34339,VERTEX_ATTRIB_ARRAY_STRIDE:34340,VERTEX_ATTRIB_ARRAY_TYPE:34341,VERTEX_ATTRIB_ARRAY_NORMALIZED:34922,VERTEX_ATTRIB_ARRAY_POINTER:34373,VERTEX_ATTRIB_ARRAY_BUFFER_BINDING:34975,COMPILE_STATUS:35713,LOW_FLOAT:36336,MEDIUM_FLOAT:36337,HIGH_FLOAT:36338,LOW_INT:36339,MEDIUM_INT:36340,HIGH_INT:36341,FRAMEBUFFER:36160,RENDERBUFFER:36161,RGBA4:32854,RGB5_A1:32855,RGB565:36194,DEPTH_COMPONENT16:33189,STENCIL_INDEX:6401,STENCIL_INDEX8:36168,DEPTH_STENCIL:34041,RENDERBUFFER_WIDTH:36162,RENDERBUFFER_HEIGHT:36163,RENDERBUFFER_INTERNAL_FORMAT:36164,RENDERBUFFER_RED_SIZE:36176,RENDERBUFFER_GREEN_SIZE:36177,RENDERBUFFER_BLUE_SIZE:36178,RENDERBUFFER_ALPHA_SIZE:36179,RENDERBUFFER_DEPTH_SIZE:36180,RENDERBUFFER_STENCIL_SIZE:36181,FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE:36048,FRAMEBUFFER_ATTACHMENT_OBJECT_NAME:36049,FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL:36050,FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE:36051,COLOR_ATTACHMENT0:36064,DEPTH_ATTACHMENT:36096,STENCIL_ATTACHMENT:36128,DEPTH_STENCIL_ATTACHMENT:33306,NONE:0,FRAMEBUFFER_COMPLETE:36053,FRAMEBUFFER_INCOMPLETE_ATTACHMENT:36054,FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:36055,FRAMEBUFFER_INCOMPLETE_DIMENSIONS:36057,FRAMEBUFFER_UNSUPPORTED:36061,FRAMEBUFFER_BINDING:36006,RENDERBUFFER_BINDING:36007,MAX_RENDERBUFFER_SIZE:34024,INVALID_FRAMEBUFFER_OPERATION:1286,UNPACK_FLIP_Y_WEBGL:37440,UNPACK_PREMULTIPLY_ALPHA_WEBGL:37441,CONTEXT_LOST_WEBGL:37442,UNPACK_COLORSPACE_CONVERSION_WEBGL:37443,BROWSER_DEFAULT_WEBGL:37444},et=$e.extend({material:null,geometry:null,mode:U.TRIANGLES,_renderInfo:null},{__program:null,lightGroup:0,renderOrder:0,culling:!0,cullFace:U.BACK,frontFace:U.CCW,frustumCulling:!0,receiveShadow:!0,castShadow:!0,ignorePicking:!1,ignorePreZ:!1,ignoreGBuffer:!1,isRenderable:function(){return this.geometry&&this.material&&this.material.shader&&!this.invisible&&this.geometry.vertexCount>0},beforeRender:function(e){},afterRender:function(e,t){},getBoundingBox:function(e,t){return t=$e.prototype.getBoundingBox.call(this,e,t),this.geometry&&this.geometry.boundingBox&&t.union(this.geometry.boundingBox),t},clone:(function(){var e=[`castShadow`,`receiveShadow`,`mode`,`culling`,`cullFace`,`frontFace`,`frustumCulling`,`renderOrder`,`lineWidth`,`ignorePicking`,`ignorePreZ`,`ignoreGBuffer`];return function(){var t=$e.prototype.clone.call(this);t.geometry=this.geometry,t.material=this.material;for(var n=0;n<e.length;n++){var r=e[n];t[r]!==this[r]&&(t[r]=this[r])}return t}})()});et.POINTS=U.POINTS,et.LINES=U.LINES,et.LINE_LOOP=U.LINE_LOOP,et.LINE_STRIP=U.LINE_STRIP,et.TRIANGLES=U.TRIANGLES,et.TRIANGLE_STRIP=U.TRIANGLE_STRIP,et.TRIANGLE_FAN=U.TRIANGLE_FAN,et.BACK=U.BACK,et.FRONT=U.FRONT,et.FRONT_AND_BACK=U.FRONT_AND_BACK,et.CW=U.CW,et.CCW=U.CCW;var tt=et.extend({skeleton:null,joints:null},function(){this.joints||(this.joints=[])},{offsetMatrix:null,isInstancedMesh:function(){return!1},isSkinnedMesh:function(){return!!(this.skeleton&&this.joints&&this.joints.length>0)},clone:function(){var e=et.prototype.clone.call(this);return e.skeleton=this.skeleton,this.joints&&(e.joints=this.joints.slice()),e}});tt.POINTS=U.POINTS,tt.LINES=U.LINES,tt.LINE_LOOP=U.LINE_LOOP,tt.LINE_STRIP=U.LINE_STRIP,tt.TRIANGLES=U.TRIANGLES,tt.TRIANGLE_STRIP=U.TRIANGLE_STRIP,tt.TRIANGLE_FAN=U.TRIANGLE_FAN,tt.BACK=U.BACK,tt.FRONT=U.FRONT,tt.FRONT_AND_BACK=U.FRONT_AND_BACK,tt.CW=U.CW,tt.CCW=U.CCW;var nt=[`OES_texture_float`,`OES_texture_half_float`,`OES_texture_float_linear`,`OES_texture_half_float_linear`,`OES_standard_derivatives`,`OES_vertex_array_object`,`OES_element_index_uint`,`WEBGL_compressed_texture_s3tc`,`WEBGL_depth_texture`,`EXT_texture_filter_anisotropic`,`EXT_shader_texture_lod`,`WEBGL_draw_buffers`,`EXT_frag_depth`,`EXT_sRGB`,`ANGLE_instanced_arrays`],rt=[`MAX_TEXTURE_SIZE`,`MAX_CUBE_MAP_TEXTURE_SIZE`];function it(e){for(var t={},n={},r=0;r<nt.length;r++){var i=nt[r];o(i)}for(var r=0;r<rt.length;r++){var a=rt[r];n[a]=e.getParameter(e[a])}this.getExtension=function(e){return e in t||o(e),t[e]},this.getParameter=function(e){return n[e]};function o(n){if(e.getExtension){var r=e.getExtension(n);r||(r=e.getExtension(`MOZ_`+n)),r||(r=e.getExtension(`WEBKIT_`+n)),t[n]=r}}}function at(e){var t=new XMLHttpRequest;t.open(`get`,e.url),t.responseType=e.responseType||`text`,e.onprogress&&(t.onprogress=function(t){if(t.lengthComputable){var n=t.loaded/t.total;e.onprogress(n,t.loaded,t.total)}else e.onprogress(null)}),t.onload=function(n){t.status>=400?e.onerror&&e.onerror():e.onload&&e.onload(t.response)},e.onerror&&(t.onerror=e.onerror),t.send(null)}var ot={get:at},st,ct={};ct.supportWebGL=function(){if(st==null)try{var e=document.createElement(`canvas`);if(!(e.getContext(`webgl`)||e.getContext(`experimental-webgl`)))throw Error()}catch(e){st=!1}return st},ct.Int8Array=typeof Int8Array>`u`?Array:Int8Array,ct.Uint8Array=typeof Uint8Array>`u`?Array:Uint8Array,ct.Uint16Array=typeof Uint16Array>`u`?Array:Uint16Array,ct.Uint32Array=typeof Uint32Array>`u`?Array:Uint32Array,ct.Int16Array=typeof Int16Array>`u`?Array:Int16Array,ct.Float32Array=typeof Float32Array>`u`?Array:Float32Array,ct.Float64Array=typeof Float64Array>`u`?Array:Float64Array;var lt={};typeof window<`u`?lt=window:typeof global<`u`&&(lt=global),ct.requestAnimationFrame=lt.requestAnimationFrame||lt.msRequestAnimationFrame||lt.mozRequestAnimationFrame||lt.webkitRequestAnimationFrame||function(e){setTimeout(e,16)},ct.createCanvas=function(){return document.createElement(`canvas`)},ct.createImage=function(){return new lt.Image},ct.request={get:ot.get},ct.addEventListener=function(e,t,n,r){e.addEventListener(t,n,r)},ct.removeEventListener=function(e,t,n){e.removeEventListener(t,n)};var ut=function(){this.head=null,this.tail=null,this._length=0};ut.prototype.insert=function(e){var t=new ut.Entry(e);return this.insertEntry(t),t},ut.prototype.insertAt=function(e,t){if(!(e<0)){for(var n=this.head,r=0;n&&r!=e;)n=n.next,r++;if(n){var i=new ut.Entry(t),a=n.prev;a?(a.next=i,i.prev=a):this.head=i,i.next=n,n.prev=i}else this.insert(t)}},ut.prototype.insertBeforeEntry=function(e,t){var n=new ut.Entry(e),r=t.prev;r?(r.next=n,n.prev=r):this.head=n,n.next=t,t.prev=n,this._length++},ut.prototype.insertEntry=function(e){this.head?(this.tail.next=e,e.prev=this.tail,this.tail=e):this.head=this.tail=e,this._length++},ut.prototype.remove=function(e){var t=e.prev,n=e.next;t?t.next=n:this.head=n,n?n.prev=t:this.tail=t,e.next=e.prev=null,this._length--},ut.prototype.removeAt=function(e){if(!(e<0)){for(var t=this.head,n=0;t&&n!=e;)t=t.next,n++;if(t)return this.remove(t),t.value}},ut.prototype.getHead=function(){if(this.head)return this.head.value},ut.prototype.getTail=function(){if(this.tail)return this.tail.value},ut.prototype.getAt=function(e){if(!(e<0)){for(var t=this.head,n=0;t&&n!=e;)t=t.next,n++;return t.value}},ut.prototype.indexOf=function(e){for(var t=this.head,n=0;t;){if(t.value===e)return n;t=t.next,n++}},ut.prototype.length=function(){return this._length},ut.prototype.isEmpty=function(){return this._length===0},ut.prototype.forEach=function(e,t){for(var n=this.head,r=0,i=t!==void 0;n;)i?e.call(t,n.value,r):e(n.value,r),n=n.next,r++},ut.prototype.clear=function(){this.tail=this.head=null,this._length=0},ut.Entry=function(e){this.value=e,this.next=null,this.prev=null};var dt=function(e){this._list=new ut,this._map={},this._maxSize=e||10};dt.prototype.setMaxSize=function(e){this._maxSize=e},dt.prototype.put=function(e,t){if(!this._map.hasOwnProperty(e)){var n=this._list.length();if(n>=this._maxSize&&n>0){var r=this._list.head;this._list.remove(r),delete this._map[r.key]}var i=this._list.insert(t);i.key=e,this._map[e]=i}},dt.prototype.get=function(e){var t=this._map[e];if(this._map.hasOwnProperty(e))return t!==this._list.tail&&(this._list.remove(t),this._list.insertEntry(t)),t.value},dt.prototype.remove=function(e){var t=this._map[e];t!==void 0&&(delete this._map[e],this._list.remove(t))},dt.prototype.clear=function(){this._list.clear(),this._map={}};var ft={},pt={transparent:[0,0,0,0],aliceblue:[240,248,255,1],antiquewhite:[250,235,215,1],aqua:[0,255,255,1],aquamarine:[127,255,212,1],azure:[240,255,255,1],beige:[245,245,220,1],bisque:[255,228,196,1],black:[0,0,0,1],blanchedalmond:[255,235,205,1],blue:[0,0,255,1],blueviolet:[138,43,226,1],brown:[165,42,42,1],burlywood:[222,184,135,1],cadetblue:[95,158,160,1],chartreuse:[127,255,0,1],chocolate:[210,105,30,1],coral:[255,127,80,1],cornflowerblue:[100,149,237,1],cornsilk:[255,248,220,1],crimson:[220,20,60,1],cyan:[0,255,255,1],darkblue:[0,0,139,1],darkcyan:[0,139,139,1],darkgoldenrod:[184,134,11,1],darkgray:[169,169,169,1],darkgreen:[0,100,0,1],darkgrey:[169,169,169,1],darkkhaki:[189,183,107,1],darkmagenta:[139,0,139,1],darkolivegreen:[85,107,47,1],darkorange:[255,140,0,1],darkorchid:[153,50,204,1],darkred:[139,0,0,1],darksalmon:[233,150,122,1],darkseagreen:[143,188,143,1],darkslateblue:[72,61,139,1],darkslategray:[47,79,79,1],darkslategrey:[47,79,79,1],darkturquoise:[0,206,209,1],darkviolet:[148,0,211,1],deeppink:[255,20,147,1],deepskyblue:[0,191,255,1],dimgray:[105,105,105,1],dimgrey:[105,105,105,1],dodgerblue:[30,144,255,1],firebrick:[178,34,34,1],floralwhite:[255,250,240,1],forestgreen:[34,139,34,1],fuchsia:[255,0,255,1],gainsboro:[220,220,220,1],ghostwhite:[248,248,255,1],gold:[255,215,0,1],goldenrod:[218,165,32,1],gray:[128,128,128,1],green:[0,128,0,1],greenyellow:[173,255,47,1],grey:[128,128,128,1],honeydew:[240,255,240,1],hotpink:[255,105,180,1],indianred:[205,92,92,1],indigo:[75,0,130,1],ivory:[255,255,240,1],khaki:[240,230,140,1],lavender:[230,230,250,1],lavenderblush:[255,240,245,1],lawngreen:[124,252,0,1],lemonchiffon:[255,250,205,1],lightblue:[173,216,230,1],lightcoral:[240,128,128,1],lightcyan:[224,255,255,1],lightgoldenrodyellow:[250,250,210,1],lightgray:[211,211,211,1],lightgreen:[144,238,144,1],lightgrey:[211,211,211,1],lightpink:[255,182,193,1],lightsalmon:[255,160,122,1],lightseagreen:[32,178,170,1],lightskyblue:[135,206,250,1],lightslategray:[119,136,153,1],lightslategrey:[119,136,153,1],lightsteelblue:[176,196,222,1],lightyellow:[255,255,224,1],lime:[0,255,0,1],limegreen:[50,205,50,1],linen:[250,240,230,1],magenta:[255,0,255,1],maroon:[128,0,0,1],mediumaquamarine:[102,205,170,1],mediumblue:[0,0,205,1],mediumorchid:[186,85,211,1],mediumpurple:[147,112,219,1],mediumseagreen:[60,179,113,1],mediumslateblue:[123,104,238,1],mediumspringgreen:[0,250,154,1],mediumturquoise:[72,209,204,1],mediumvioletred:[199,21,133,1],midnightblue:[25,25,112,1],mintcream:[245,255,250,1],mistyrose:[255,228,225,1],moccasin:[255,228,181,1],navajowhite:[255,222,173,1],navy:[0,0,128,1],oldlace:[253,245,230,1],olive:[128,128,0,1],olivedrab:[107,142,35,1],orange:[255,165,0,1],orangered:[255,69,0,1],orchid:[218,112,214,1],palegoldenrod:[238,232,170,1],palegreen:[152,251,152,1],paleturquoise:[175,238,238,1],palevioletred:[219,112,147,1],papayawhip:[255,239,213,1],peachpuff:[255,218,185,1],peru:[205,133,63,1],pink:[255,192,203,1],plum:[221,160,221,1],powderblue:[176,224,230,1],purple:[128,0,128,1],red:[255,0,0,1],rosybrown:[188,143,143,1],royalblue:[65,105,225,1],saddlebrown:[139,69,19,1],salmon:[250,128,114,1],sandybrown:[244,164,96,1],seagreen:[46,139,87,1],seashell:[255,245,238,1],sienna:[160,82,45,1],silver:[192,192,192,1],skyblue:[135,206,235,1],slateblue:[106,90,205,1],slategray:[112,128,144,1],slategrey:[112,128,144,1],snow:[255,250,250,1],springgreen:[0,255,127,1],steelblue:[70,130,180,1],tan:[210,180,140,1],teal:[0,128,128,1],thistle:[216,191,216,1],tomato:[255,99,71,1],turquoise:[64,224,208,1],violet:[238,130,238,1],wheat:[245,222,179,1],white:[255,255,255,1],whitesmoke:[245,245,245,1],yellow:[255,255,0,1],yellowgreen:[154,205,50,1]};function mt(e){return e=Math.round(e),e<0?0:e>255?255:e}function ht(e){return e=Math.round(e),e<0?0:e>360?360:e}function gt(e){return e<0?0:e>1?1:e}function _t(e){return e.length&&e.charAt(e.length-1)===`%`?mt(parseFloat(e)/100*255):mt(parseInt(e,10))}function vt(e){return e.length&&e.charAt(e.length-1)===`%`?gt(parseFloat(e)/100):gt(parseFloat(e))}function yt(e,t,n){return n<0?n+=1:n>1&&--n,n*6<1?e+(t-e)*n*6:n*2<1?t:n*3<2?e+(t-e)*(2/3-n)*6:e}function bt(e,t,n){return e+(t-e)*n}function xt(e,t,n,r,i){return e[0]=t,e[1]=n,e[2]=r,e[3]=i,e}function St(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e}var Ct=new dt(20),wt=null;function Tt(e,t){wt&&St(wt,t),wt=Ct.put(e,wt||t.slice())}ft.parse=function(e,t){if(e){t=t||[];var n=Ct.get(e);if(n)return St(t,n);e+=``;var r=e.replace(/ /g,``).toLowerCase();if(r in pt)return St(t,pt[r]),Tt(e,t),t;if(r.charAt(0)===`#`){if(r.length===4){var i=parseInt(r.substr(1),16);if(!(i>=0&&i<=4095)){xt(t,0,0,0,1);return}return xt(t,(i&3840)>>4|(i&3840)>>8,i&240|(i&240)>>4,i&15|(i&15)<<4,1),Tt(e,t),t}else if(r.length===7){var i=parseInt(r.substr(1),16);if(!(i>=0&&i<=16777215)){xt(t,0,0,0,1);return}return xt(t,(i&16711680)>>16,(i&65280)>>8,i&255,1),Tt(e,t),t}return}var a=r.indexOf(`(`),o=r.indexOf(`)`);if(a!==-1&&o+1===r.length){var s=r.substr(0,a),c=r.substr(a+1,o-(a+1)).split(`,`),l=1;switch(s){case`rgba`:if(c.length!==4){xt(t,0,0,0,1);return}l=vt(c.pop());case`rgb`:if(c.length!==3){xt(t,0,0,0,1);return}return xt(t,_t(c[0]),_t(c[1]),_t(c[2]),l),Tt(e,t),t;case`hsla`:if(c.length!==4){xt(t,0,0,0,1);return}return c[3]=vt(c[3]),Et(c,t),Tt(e,t),t;case`hsl`:if(c.length!==3){xt(t,0,0,0,1);return}return Et(c,t),Tt(e,t),t;default:return}}xt(t,0,0,0,1)}},ft.parseToFloat=function(e,t){if(t=ft.parse(e,t),t)return t[0]/=255,t[1]/=255,t[2]/=255,t};function Et(e,t){var n=(parseFloat(e[0])%360+360)%360/360,r=vt(e[1]),i=vt(e[2]),a=i<=.5?i*(r+1):i+r-i*r,o=i*2-a;return t=t||[],xt(t,mt(yt(o,a,n+1/3)*255),mt(yt(o,a,n)*255),mt(yt(o,a,n-1/3)*255),1),e.length===4&&(t[3]=e[3]),t}function Dt(e){if(e){var t=e[0]/255,n=e[1]/255,r=e[2]/255,i=Math.min(t,n,r),a=Math.max(t,n,r),o=a-i,s=(a+i)/2,c,l;if(o===0)c=0,l=0;else{l=s<.5?o/(a+i):o/(2-a-i);var u=((a-t)/6+o/2)/o,d=((a-n)/6+o/2)/o,f=((a-r)/6+o/2)/o;t===a?c=f-d:n===a?c=1/3+u-f:r===a&&(c=2/3+d-u),c<0&&(c+=1),c>1&&--c}var p=[c*360,l,s];return e[3]!=null&&p.push(e[3]),p}}ft.lift=function(e,t){var n=ft.parse(e);if(n){for(var r=0;r<3;r++)t<0?n[r]=n[r]*(1-t)|0:n[r]=(255-n[r])*t+n[r]|0;return ft.stringify(n,n.length===4?`rgba`:`rgb`)}},ft.toHex=function(e){var t=ft.parse(e);if(t)return((1<<24)+(t[0]<<16)+(t[1]<<8)+ +t[2]).toString(16).slice(1)},ft.fastLerp=function(e,t,n){if(!(!(t&&t.length)||!(e>=0&&e<=1))){n=n||[];var r=e*(t.length-1),i=Math.floor(r),a=Math.ceil(r),o=t[i],s=t[a],c=r-i;return n[0]=mt(bt(o[0],s[0],c)),n[1]=mt(bt(o[1],s[1],c)),n[2]=mt(bt(o[2],s[2],c)),n[3]=gt(bt(o[3],s[3],c)),n}},ft.fastMapToColor=ft.fastLerp,ft.lerp=function(e,t,n){if(!(!(t&&t.length)||!(e>=0&&e<=1))){var r=e*(t.length-1),i=Math.floor(r),a=Math.ceil(r),o=ft.parse(t[i]),s=ft.parse(t[a]),c=r-i,l=ft.stringify([mt(bt(o[0],s[0],c)),mt(bt(o[1],s[1],c)),mt(bt(o[2],s[2],c)),gt(bt(o[3],s[3],c))],`rgba`);return n?{color:l,leftIndex:i,rightIndex:a,value:r}:l}},ft.mapToColor=ft.lerp,ft.modifyHSL=function(e,t,n,r){if(e=ft.parse(e),e)return e=Dt(e),t!=null&&(e[0]=ht(t)),n!=null&&(e[1]=vt(n)),r!=null&&(e[2]=vt(r)),ft.stringify(Et(e),`rgba`)},ft.modifyAlpha=function(e,t){if(e=ft.parse(e),e&&t!=null)return e[3]=gt(t),ft.stringify(e,`rgba`)},ft.stringify=function(e,t){if(!(!e||!e.length)){var n=e[0]+`,`+e[1]+`,`+e[2];return(t===`rgba`||t===`hsva`||t===`hsla`)&&(n+=`,`+e[3]),t+`(`+n+`)`}};var Ot=ft.parseToFloat,kt={};function At(e){var t=Object.keys(e);t.sort();for(var n=[],r=0;r<t.length;r++){var i=t[r],a=e[i];a===null?n.push(i):n.push(i+` `+a.toString())}return n.join(`
`)}function jt(e,t,n){n.sort();for(var r=[],i=0;i<n.length;i++){var a=n[i];r.push(a)}var o=At(e)+`
`+At(t)+`
`+r.join(`
`);if(kt[o])return kt[o];var s=Pe.genGUID();return kt[o]=s,s}var Mt=Fe.extend(function(){return{name:``,depthTest:!0,depthMask:!0,transparent:!1,blend:null,autoUpdateTextureStatus:!0,uniforms:{},vertexDefines:{},fragmentDefines:{},_textureStatus:{},_enabledUniforms:null}},function(){this.name||(this.name=`MATERIAL_`+this.__uid__),this.shader&&this.attachShader(this.shader,!0)},{precision:`highp`,setUniform:function(e,t){t===void 0&&console.warn(`Uniform value "`+e+`" is undefined`);var n=this.uniforms[e];n&&(typeof t==`string`&&(t=Ot(t)||t),n.value=t,this.autoUpdateTextureStatus&&n.type===`t`&&(t?this.enableTexture(e):this.disableTexture(e)))},setUniforms:function(e){for(var t in e){var n=e[t];this.setUniform(t,n)}},isUniformEnabled:function(e){return this._enabledUniforms.indexOf(e)>=0},getEnabledUniforms:function(){return this._enabledUniforms},getTextureUniforms:function(){return this._textureUniforms},set:function(e,t){if(typeof e==`object`)for(var n in e){var r=e[n];this.setUniform(n,r)}else this.setUniform(e,t)},get:function(e){var t=this.uniforms[e];if(t)return t.value},attachShader:function(e,t){var n=this.uniforms;this.uniforms=e.createUniforms(),this.shader=e;var r=this.uniforms;this._enabledUniforms=Object.keys(r),this._enabledUniforms.sort(),this._textureUniforms=this._enabledUniforms.filter(function(e){var t=this.uniforms[e].type;return t===`t`||t===`tv`},this);var i=this.vertexDefines,a=this.fragmentDefines;if(this.vertexDefines=Pe.clone(e.vertexDefines),this.fragmentDefines=Pe.clone(e.fragmentDefines),t){for(var o in n)r[o]&&(r[o].value=n[o].value);Pe.defaults(this.vertexDefines,i),Pe.defaults(this.fragmentDefines,a)}var s={};for(var c in e.textures)s[c]={shaderType:e.textures[c].shaderType,type:e.textures[c].type,enabled:t&&this._textureStatus[c]?this._textureStatus[c].enabled:!1};this._textureStatus=s,this._programKey=``},clone:function(){var e=new this.constructor({name:this.name,shader:this.shader});for(var t in this.uniforms)e.uniforms[t].value=this.uniforms[t].value;return e.depthTest=this.depthTest,e.depthMask=this.depthMask,e.transparent=this.transparent,e.blend=this.blend,e.vertexDefines=Pe.clone(this.vertexDefines),e.fragmentDefines=Pe.clone(this.fragmentDefines),e.enableTexture(this.getEnabledTextures()),e.precision=this.precision,e},define:function(e,t,n){var r=this.vertexDefines,i=this.fragmentDefines;e!==`vertex`&&e!==`fragment`&&e!==`both`&&arguments.length<3&&(n=t,t=e,e=`both`),n=n==null?null:n,(e===`vertex`||e===`both`)&&r[t]!==n&&(r[t]=n,this._programKey=``),(e===`fragment`||e===`both`)&&i[t]!==n&&(i[t]=n,e!==`both`&&(this._programKey=``))},undefine:function(e,t){e!==`vertex`&&e!==`fragment`&&e!==`both`&&arguments.length<2&&(t=e,e=`both`),(e===`vertex`||e===`both`)&&this.isDefined(`vertex`,t)&&(delete this.vertexDefines[t],this._programKey=``),(e===`fragment`||e===`both`)&&this.isDefined(`fragment`,t)&&(delete this.fragmentDefines[t],e!==`both`&&(this._programKey=``))},isDefined:function(e,t){switch(e){case`vertex`:return this.vertexDefines[t]!==void 0;case`fragment`:return this.fragmentDefines[t]!==void 0}},getDefine:function(e,t){switch(e){case`vertex`:return this.vertexDefines[t];case`fragment`:return this.fragmentDefines[t]}},enableTexture:function(e){if(Array.isArray(e)){for(var t=0;t<e.length;t++)this.enableTexture(e[t]);return}var n=this._textureStatus[e];n&&(n.enabled||(n.enabled=!0,this._programKey=``))},enableTexturesAll:function(){var e=this._textureStatus;for(var t in e)e[t].enabled=!0;this._programKey=``},disableTexture:function(e){if(Array.isArray(e)){for(var t=0;t<e.length;t++)this.disableTexture(e[t]);return}var n=this._textureStatus[e];n&&n.enabled&&(n.enabled=!1,this._programKey=``)},disableTexturesAll:function(){var e=this._textureStatus;for(var t in e)e[t].enabled=!1;this._programKey=``},isTextureEnabled:function(e){var t=this._textureStatus;return!!t[e]&&t[e].enabled},getEnabledTextures:function(){var e=[],t=this._textureStatus;for(var n in t)t[n].enabled&&e.push(n);return e},dirtyDefines:function(){this._programKey=``},getProgramKey:function(){return this._programKey||(this._programKey=jt(this.vertexDefines,this.fragmentDefines,this.getEnabledTextures())),this._programKey}}),W={};W.create=function(){var e=new Ie(2);return e[0]=0,e[1]=0,e},W.clone=function(e){var t=new Ie(2);return t[0]=e[0],t[1]=e[1],t},W.fromValues=function(e,t){var n=new Ie(2);return n[0]=e,n[1]=t,n},W.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e},W.set=function(e,t,n){return e[0]=t,e[1]=n,e},W.add=function(e,t,n){return e[0]=t[0]+n[0],e[1]=t[1]+n[1],e},W.subtract=function(e,t,n){return e[0]=t[0]-n[0],e[1]=t[1]-n[1],e},W.sub=W.subtract,W.multiply=function(e,t,n){return e[0]=t[0]*n[0],e[1]=t[1]*n[1],e},W.mul=W.multiply,W.divide=function(e,t,n){return e[0]=t[0]/n[0],e[1]=t[1]/n[1],e},W.div=W.divide,W.min=function(e,t,n){return e[0]=Math.min(t[0],n[0]),e[1]=Math.min(t[1],n[1]),e},W.max=function(e,t,n){return e[0]=Math.max(t[0],n[0]),e[1]=Math.max(t[1],n[1]),e},W.scale=function(e,t,n){return e[0]=t[0]*n,e[1]=t[1]*n,e},W.scaleAndAdd=function(e,t,n,r){return e[0]=t[0]+n[0]*r,e[1]=t[1]+n[1]*r,e},W.distance=function(e,t){var n=t[0]-e[0],r=t[1]-e[1];return Math.sqrt(n*n+r*r)},W.dist=W.distance,W.squaredDistance=function(e,t){var n=t[0]-e[0],r=t[1]-e[1];return n*n+r*r},W.sqrDist=W.squaredDistance,W.length=function(e){var t=e[0],n=e[1];return Math.sqrt(t*t+n*n)},W.len=W.length,W.squaredLength=function(e){var t=e[0],n=e[1];return t*t+n*n},W.sqrLen=W.squaredLength,W.negate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e},W.inverse=function(e,t){return e[0]=1/t[0],e[1]=1/t[1],e},W.normalize=function(e,t){var n=t[0],r=t[1],i=n*n+r*r;return i>0&&(i=1/Math.sqrt(i),e[0]=t[0]*i,e[1]=t[1]*i),e},W.dot=function(e,t){return e[0]*t[0]+e[1]*t[1]},W.cross=function(e,t,n){var r=t[0]*n[1]-t[1]*n[0];return e[0]=e[1]=0,e[2]=r,e},W.lerp=function(e,t,n,r){var i=t[0],a=t[1];return e[0]=i+r*(n[0]-i),e[1]=a+r*(n[1]-a),e},W.random=function(e,t){t=t||1;var n=GLMAT_RANDOM()*2*Math.PI;return e[0]=Math.cos(n)*t,e[1]=Math.sin(n)*t,e},W.transformMat2=function(e,t,n){var r=t[0],i=t[1];return e[0]=n[0]*r+n[2]*i,e[1]=n[1]*r+n[3]*i,e},W.transformMat2d=function(e,t,n){var r=t[0],i=t[1];return e[0]=n[0]*r+n[2]*i+n[4],e[1]=n[1]*r+n[3]*i+n[5],e},W.transformMat3=function(e,t,n){var r=t[0],i=t[1];return e[0]=n[0]*r+n[3]*i+n[6],e[1]=n[1]*r+n[4]*i+n[7],e},W.transformMat4=function(e,t,n){var r=t[0],i=t[1];return e[0]=n[0]*r+n[4]*i+n[12],e[1]=n[1]*r+n[5]*i+n[13],e},W.forEach=(function(){var e=W.create();return function(t,n,r,i,a,o){var s,c;for(n||(n=2),r||(r=0),c=i?Math.min(i*n+r,t.length):t.length,s=r;s<c;s+=n)e[0]=t[s],e[1]=t[s+1],a(e,e,o),t[s]=e[0],t[s+1]=e[1];return t}})();var G=function(e,t){e=e||0,t=t||0,this.array=W.fromValues(e,t),this._dirty=!0};if(G.prototype={constructor:G,add:function(e){return W.add(this.array,this.array,e.array),this._dirty=!0,this},set:function(e,t){return this.array[0]=e,this.array[1]=t,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this._dirty=!0,this},clone:function(){return new G(this.x,this.y)},copy:function(e){return W.copy(this.array,e.array),this._dirty=!0,this},cross:function(e,t){return W.cross(e.array,this.array,t.array),e._dirty=!0,this},dist:function(e){return W.dist(this.array,e.array)},distance:function(e){return W.distance(this.array,e.array)},div:function(e){return W.div(this.array,this.array,e.array),this._dirty=!0,this},divide:function(e){return W.divide(this.array,this.array,e.array),this._dirty=!0,this},dot:function(e){return W.dot(this.array,e.array)},len:function(){return W.len(this.array)},length:function(){return W.length(this.array)},lerp:function(e,t,n){return W.lerp(this.array,e.array,t.array,n),this._dirty=!0,this},min:function(e){return W.min(this.array,this.array,e.array),this._dirty=!0,this},max:function(e){return W.max(this.array,this.array,e.array),this._dirty=!0,this},mul:function(e){return W.mul(this.array,this.array,e.array),this._dirty=!0,this},multiply:function(e){return W.multiply(this.array,this.array,e.array),this._dirty=!0,this},negate:function(){return W.negate(this.array,this.array),this._dirty=!0,this},normalize:function(){return W.normalize(this.array,this.array),this._dirty=!0,this},random:function(e){return W.random(this.array,e),this._dirty=!0,this},scale:function(e){return W.scale(this.array,this.array,e),this._dirty=!0,this},scaleAndAdd:function(e,t){return W.scaleAndAdd(this.array,this.array,e.array,t),this._dirty=!0,this},sqrDist:function(e){return W.sqrDist(this.array,e.array)},squaredDistance:function(e){return W.squaredDistance(this.array,e.array)},sqrLen:function(){return W.sqrLen(this.array)},squaredLength:function(){return W.squaredLength(this.array)},sub:function(e){return W.sub(this.array,this.array,e.array),this._dirty=!0,this},subtract:function(e){return W.subtract(this.array,this.array,e.array),this._dirty=!0,this},transformMat2:function(e){return W.transformMat2(this.array,this.array,e.array),this._dirty=!0,this},transformMat2d:function(e){return W.transformMat2d(this.array,this.array,e.array),this._dirty=!0,this},transformMat3:function(e){return W.transformMat3(this.array,this.array,e.array),this._dirty=!0,this},transformMat4:function(e){return W.transformMat4(this.array,this.array,e.array),this._dirty=!0,this},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}},Object.defineProperty){var Nt=G.prototype;Object.defineProperty(Nt,"x",{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),Object.defineProperty(Nt,"y",{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}})}G.add=function(e,t,n){return W.add(e.array,t.array,n.array),e._dirty=!0,e},G.set=function(e,t,n){return W.set(e.array,t,n),e._dirty=!0,e},G.copy=function(e,t){return W.copy(e.array,t.array),e._dirty=!0,e},G.cross=function(e,t,n){return W.cross(e.array,t.array,n.array),e._dirty=!0,e},G.dist=function(e,t){return W.distance(e.array,t.array)},G.distance=G.dist,G.div=function(e,t,n){return W.divide(e.array,t.array,n.array),e._dirty=!0,e},G.divide=G.div,G.dot=function(e,t){return W.dot(e.array,t.array)},G.len=function(e){return W.length(e.array)},G.lerp=function(e,t,n,r){return W.lerp(e.array,t.array,n.array,r),e._dirty=!0,e},G.min=function(e,t,n){return W.min(e.array,t.array,n.array),e._dirty=!0,e},G.max=function(e,t,n){return W.max(e.array,t.array,n.array),e._dirty=!0,e},G.mul=function(e,t,n){return W.multiply(e.array,t.array,n.array),e._dirty=!0,e},G.multiply=G.mul,G.negate=function(e,t){return W.negate(e.array,t.array),e._dirty=!0,e},G.normalize=function(e,t){return W.normalize(e.array,t.array),e._dirty=!0,e},G.random=function(e,t){return W.random(e.array,t),e._dirty=!0,e},G.scale=function(e,t,n){return W.scale(e.array,t.array,n),e._dirty=!0,e},G.scaleAndAdd=function(e,t,n,r){return W.scaleAndAdd(e.array,t.array,n.array,r),e._dirty=!0,e},G.sqrDist=function(e,t){return W.sqrDist(e.array,t.array)},G.squaredDistance=G.sqrDist,G.sqrLen=function(e){return W.sqrLen(e.array)},G.squaredLength=G.sqrLen,G.sub=function(e,t,n){return W.subtract(e.array,t.array,n.array),e._dirty=!0,e},G.subtract=G.sub,G.transformMat2=function(e,t,n){return W.transformMat2(e.array,t.array,n.array),e._dirty=!0,e},G.transformMat2d=function(e,t,n){return W.transformMat2d(e.array,t.array,n.array),e._dirty=!0,e},G.transformMat3=function(e,t,n){return W.transformMat3(e.array,t.array,n.array),e._dirty=!0,e},G.transformMat4=function(e,t,n){return W.transformMat4(e.array,t.array,n.array),e._dirty=!0,e};var Pt=1,Ft=2,It=3,Lt={};function Rt(e){for(var t=e.split(`
`),n=0,r=t.length;n<r;n++)t[n]=n+1+`: `+t[n];return t.join(`
`)}function zt(e,t,n){if(!e.getShaderParameter(t,e.COMPILE_STATUS))return[e.getShaderInfoLog(t),Rt(n)].join(`
`)}var Bt=new ct.Float32Array(16),Vt=Fe.extend({uniformSemantics:{},attributes:{}},function(){this._locations={},this._textureSlot=0,this._program=null},{bind:function(e){this._textureSlot=0,e.gl.useProgram(this._program)},hasUniform:function(e){return this._locations[e]!=null},useTextureSlot:function(e,t,n){t&&(e.gl.activeTexture(e.gl.TEXTURE0+n),t.isRenderable()?t.bind(e):t.unbind(e))},currentTextureSlot:function(){return this._textureSlot},resetTextureSlot:function(e){this._textureSlot=e||0},takeCurrentTextureSlot:function(e,t){var n=this._textureSlot;return this.useTextureSlot(e,t,n),this._textureSlot++,n},setUniform:function(e,t,n,r){var i=this._locations[n];if(i==null)return!1;switch(t){case`m4`:if(!(r instanceof Float32Array)){for(var a=0;a<r.length;a++)Bt[a]=r[a];r=Bt}e.uniformMatrix4fv(i,!1,r);break;case`2i`:e.uniform2i(i,r[0],r[1]);break;case`2f`:e.uniform2f(i,r[0],r[1]);break;case`3i`:e.uniform3i(i,r[0],r[1],r[2]);break;case`3f`:e.uniform3f(i,r[0],r[1],r[2]);break;case`4i`:e.uniform4i(i,r[0],r[1],r[2],r[3]);break;case`4f`:e.uniform4f(i,r[0],r[1],r[2],r[3]);break;case`1i`:e.uniform1i(i,r);break;case`1f`:e.uniform1f(i,r);break;case`1fv`:e.uniform1fv(i,r);break;case`1iv`:e.uniform1iv(i,r);break;case`2iv`:e.uniform2iv(i,r);break;case`2fv`:e.uniform2fv(i,r);break;case`3iv`:e.uniform3iv(i,r);break;case`3fv`:e.uniform3fv(i,r);break;case`4iv`:e.uniform4iv(i,r);break;case`4fv`:e.uniform4fv(i,r);break;case`m2`:case`m2v`:e.uniformMatrix2fv(i,!1,r);break;case`m3`:case`m3v`:e.uniformMatrix3fv(i,!1,r);break;case`m4v`:if(Array.isArray(r)&&Array.isArray(r[0])){for(var o=new ct.Float32Array(r.length*16),s=0,a=0;a<r.length;a++)for(var c=r[a],l=0;l<16;l++)o[s++]=c[l];e.uniformMatrix4fv(i,!1,o)}else e.uniformMatrix4fv(i,!1,r);break}return!0},setUniformOfSemantic:function(e,t,n){var r=this.uniformSemantics[t];return r?this.setUniform(e,r.type,r.symbol,n):!1},enableAttributes:function(e,t,n){var r=e.gl,i=this._program,a=this._locations,o=n?n.__enabledAttributeList:Lt[e.__uid__];o||(o=n?n.__enabledAttributeList=[]:Lt[e.__uid__]=[]);for(var s=[],c=0;c<t.length;c++){var l=t[c];if(!this.attributes[l]){s[c]=-1;continue}var u=a[l];if(u==null){if(u=r.getAttribLocation(i,l),u===-1){s[c]=-1;continue}a[l]=u}s[c]=u,o[u]?o[u]=Ft:o[u]=Pt}for(var c=0;c<o.length;c++)switch(o[c]){case Pt:r.enableVertexAttribArray(c),o[c]=It;break;case Ft:o[c]=It;break;case It:r.disableVertexAttribArray(c),o[c]=0;break}return s},getAttribLocation:function(e,t){var n=this._locations,r=n[t];return r==null&&(r=e.getAttribLocation(this._program,t),n[t]=r),r},buildProgram:function(e,t,n,r){var i=e.createShader(e.VERTEX_SHADER),a=e.createProgram();e.shaderSource(i,n),e.compileShader(i);var o=e.createShader(e.FRAGMENT_SHADER);e.shaderSource(o,r),e.compileShader(o);var s=zt(e,i,n);if(s||(s=zt(e,o,r),s))return s;if(e.attachShader(a,i),e.attachShader(a,o),t.attributeSemantics.POSITION)e.bindAttribLocation(a,0,t.attributeSemantics.POSITION.symbol);else{var c=Object.keys(this.attributes);e.bindAttribLocation(a,0,c[0])}if(e.linkProgram(a),e.deleteShader(i),e.deleteShader(o),this._program=a,this.vertexCode=n,this.fragmentCode=r,!e.getProgramParameter(a,e.LINK_STATUS))return`Could not link program
`+e.getProgramInfoLog(a);for(var l=0;l<t.uniforms.length;l++){var u=t.uniforms[l];this._locations[u]=e.getUniformLocation(a,u)}}}),Ht=/for\s*?\(int\s*?_idx_\s*\=\s*([\w-]+)\;\s*_idx_\s*<\s*([\w-]+);\s*_idx_\s*\+\+\s*\)\s*\{\{([\s\S]+?)(?=\}\})\}\}/g;function Ut(e,t,n){function r(e,n,r,a){var o=``;isNaN(n)&&(n=n in t?t[n]:i[n]),isNaN(r)&&(r=r in t?t[r]:i[r]);for(var s=parseInt(n);s<parseInt(r);s++)o+=`{`+a.replace(/float\s*\(\s*_idx_\s*\)/g,s.toFixed(1)).replace(/_idx_/g,s)+`}`;return o}var i={};for(var a in n)i[a+`_COUNT`]=n[a];return e.replace(Ht,r)}function Wt(e,t,n){var r=[];if(t)for(var i in t){var a=t[i];a>0&&r.push(`#define `+i.toUpperCase()+`_COUNT `+a)}if(n)for(var o=0;o<n.length;o++){var s=n[o];r.push(`#define `+s.toUpperCase()+`_ENABLED`)}for(var s in e){var c=e[s];c===null?r.push(`#define `+s):r.push(`#define `+s+` `+c.toString())}return r.join(`
`)}function Gt(e){for(var t=[],n=0;n<e.length;n++)t.push(`#extension GL_`+e[n]+` : enable`);return t.join(`
`)}function Kt(e){return[`precision`,e,`float`].join(` `)+`;
`+[`precision`,e,`int`].join(` `)+`;
`+[`precision`,e,`sampler2D`].join(` `)+`;
`}function qt(e){this._renderer=e,this._cache={}}qt.prototype.getProgram=function(e,t,n){var r=this._cache,i=e.isSkinnedMesh&&e.isSkinnedMesh(),a=e.isInstancedMesh&&e.isInstancedMesh(),o=`s`+t.shader.shaderID+`m`+t.getProgramKey();n&&(o+=`se`+n.getProgramKey(e.lightGroup)),i&&(o+=`,sk`+e.joints.length),a&&(o+=`,is`);var s=r[o];if(s)return s;var c=n?n.getLightsNumbers(e.lightGroup):{},l=this._renderer,u=l.gl,d=t.getEnabledTextures(),f=``;if(i){var p={SKINNING:null,JOINT_COUNT:e.joints.length};e.joints.length>l.getMaxJointNumber()&&(p.USE_SKIN_MATRICES_TEXTURE=null),f+=`
`+Wt(p)+`
`}a&&(f+=`
#define INSTANCING
`);var m=f+Wt(t.vertexDefines,c,d),h=f+Wt(t.fragmentDefines,c,d),g=m+`
`+t.shader.vertex,_=[`OES_standard_derivatives`,`EXT_shader_texture_lod`].filter(function(e){return l.getGLExtension(e)!=null});_.indexOf(`EXT_shader_texture_lod`)>=0&&(h+=`
#define SUPPORT_TEXTURE_LOD`),_.indexOf(`OES_standard_derivatives`)>=0&&(h+=`
#define SUPPORT_STANDARD_DERIVATIVES`);var v=Gt(_)+`
`+Kt(t.precision)+`
`+h+`
`+t.shader.fragment,y=Ut(g,t.vertexDefines,c),b=Ut(v,t.fragmentDefines,c),s=new Vt;return s.uniformSemantics=t.shader.uniformSemantics,s.attributes=t.shader.attributes,s.__error=s.buildProgram(u,t.shader,y,b),r[o]=s,s};var Jt=/uniform\s+(bool|float|int|vec2|vec3|vec4|ivec2|ivec3|ivec4|mat2|mat3|mat4|sampler2D|samplerCube)\s+([\s\S]*?);/g,Yt=/attribute\s+(float|int|vec2|vec3|vec4)\s+([\s\S]*?);/g,Xt=/#define\s+(\w+)?(\s+[\d-.]+)?\s*;?\s*\n/g,Zt={bool:`1i`,int:`1i`,sampler2D:`t`,samplerCube:`t`,float:`1f`,vec2:`2f`,vec3:`3f`,vec4:`4f`,ivec2:`2i`,ivec3:`3i`,ivec4:`4i`,mat2:`m2`,mat3:`m3`,mat4:`m4`};function Qt(e){for(var t=[],n=0;n<e;n++)t[n]=0;return t}var $t={bool:function(){return!0},int:function(){return 0},float:function(){return 0},sampler2D:function(){return null},samplerCube:function(){return null},vec2:function(){return Qt(2)},vec3:function(){return Qt(3)},vec4:function(){return Qt(4)},ivec2:function(){return Qt(2)},ivec3:function(){return Qt(3)},ivec4:function(){return Qt(4)},mat2:function(){return Qt(4)},mat3:function(){return Qt(9)},mat4:function(){return Qt(16)},array:function(){return[]}},en=[`POSITION`,`NORMAL`,`BINORMAL`,`TANGENT`,`TEXCOORD`,`TEXCOORD_0`,`TEXCOORD_1`,`COLOR`,`JOINT`,`WEIGHT`],tn=[`SKIN_MATRIX`,`VIEWPORT_SIZE`,`VIEWPORT`,`DEVICEPIXELRATIO`,`WINDOW_SIZE`,`NEAR`,`FAR`,`TIME`],nn=[`WORLD`,`VIEW`,`PROJECTION`,`WORLDVIEW`,`VIEWPROJECTION`,`WORLDVIEWPROJECTION`,`WORLDINVERSE`,`VIEWINVERSE`,`PROJECTIONINVERSE`,`WORLDVIEWINVERSE`,`VIEWPROJECTIONINVERSE`,`WORLDVIEWPROJECTIONINVERSE`,`WORLDTRANSPOSE`,`VIEWTRANSPOSE`,`PROJECTIONTRANSPOSE`,`WORLDVIEWTRANSPOSE`,`VIEWPROJECTIONTRANSPOSE`,`WORLDVIEWPROJECTIONTRANSPOSE`,`WORLDINVERSETRANSPOSE`,`VIEWINVERSETRANSPOSE`,`PROJECTIONINVERSETRANSPOSE`,`WORLDVIEWINVERSETRANSPOSE`,`VIEWPROJECTIONINVERSETRANSPOSE`,`WORLDVIEWPROJECTIONINVERSETRANSPOSE`],rn={vec4:4,vec3:3,vec2:2,float:1},an={},on={};function sn(e,t){var n=`vertex:`+e+`fragment:`+t;if(an[n])return an[n];var r=Pe.genGUID();return an[n]=r,on[r]={vertex:e,fragment:t},r}function cn(e){return e.replace(/[ \t]*\/\/.*\n/g,``).replace(/[ \t]*\/\*[\s\S]*?\*\//g,``)}function ln(){console.error(`Wrong uniform/attributes syntax`)}function un(e,t){for(var n=/[,=\(\):]/,r=t.replace(/:\s*\[\s*(.*)\s*\]/g,`=`+e+`($1)`).replace(/\s+/g,``).split(/(?=[,=\(\):])/g),i=[],a=0;a<r.length;a++)r[a].match(n)?i.push(r[a].charAt(0),r[a].slice(1)):i.push(r[a]);r=i;var o=0,s=1,c=2,l=3,u=4,d=5,f=o,p={},m=null,h;g(r[0]);function g(e){e||ln();var t=e.match(/\[(.*?)\]/);h=e.replace(/\[(.*?)\]/,``),p[h]={},t&&(p[h].isArray=!0,p[h].arraySize=t[1])}for(var a=1;a<r.length;a++){var _=r[a];if(_){if(_===`=`){if(f!==o&&f!==l){ln();break}f=s;continue}else if(_===`:`){f=u;continue}else if(_===`,`){if(f===c){if(!(m instanceof Array)){ln();break}m.push(+r[++a])}else f=d;continue}else if(_===`)`){p[h].value=new ct.Float32Array(m),m=null,f=d;continue}else if(_===`(`){if(f!==c){ln();break}if(!(m instanceof Array)){ln();break}m.push(+r[++a]);continue}else if(_.indexOf(`vec`)>=0){if(f!==s&&f!==u){ln();break}f=c,m=[];continue}else if(f===s){e===`bool`?p[h].value=_===`true`:p[h].value=parseFloat(_),m=null;continue}else if(f===u){var v=_;en.indexOf(v)>=0||tn.indexOf(v)>=0||nn.indexOf(v)>=0?p[h].semantic=v:v===`ignore`||v===`unconfigurable`?p[h].ignore=!0:e===`bool`?p[h].value=v===`true`:p[h].value=parseFloat(v);continue}g(_),f=o}}return p}function K(e,t){typeof e==`object`&&(t=e.fragment,e=e.vertex),e=cn(e),t=cn(t),this._shaderID=sn(e,t),this._vertexCode=K.parseImport(e),this._fragmentCode=K.parseImport(t),this.attributeSemantics={},this.matrixSemantics={},this.uniformSemantics={},this.matrixSemanticKeys=[],this.uniformTemplates={},this.attributes={},this.textures={},this.vertexDefines={},this.fragmentDefines={},this._parseAttributes(),this._parseUniforms(),this._parseDefines()}K.prototype={constructor:K,createUniforms:function(){var e={};for(var t in this.uniformTemplates){var n=this.uniformTemplates[t];e[t]={type:n.type,value:n.value()}}return e},_parseImport:function(){this._vertexCode=K.parseImport(this.vertex),this._fragmentCode=K.parseImport(this.fragment)},_addSemanticUniform:function(e,t,n){if(en.indexOf(n)>=0)this.attributeSemantics[n]={symbol:e,type:t};else if(nn.indexOf(n)>=0){var r=!1,i=n;n.match(/TRANSPOSE$/)&&(r=!0,i=n.slice(0,-9)),this.matrixSemantics[n]={symbol:e,type:t,isTranspose:r,semanticNoTranspose:i}}else tn.indexOf(n)>=0&&(this.uniformSemantics[n]={symbol:e,type:t})},_addMaterialUniform:function(e,t,n,r,i,a){a[e]={type:n,value:i?$t.array:r||$t[t],semantic:null}},_parseUniforms:function(){var e={},t=this,n=`vertex`;this._uniformList=[],this._vertexCode=this._vertexCode.replace(Jt,i),n=`fragment`,this._fragmentCode=this._fragmentCode.replace(Jt,i),t.matrixSemanticKeys=Object.keys(this.matrixSemantics);function r(e){return e==null?null:function(){return e}}function i(i,a,o){var s=un(a,o),c=[];for(var l in s){var u=s[l],d=u.semantic,f=l,p=Zt[a],m=r(s[l].value);s[l].isArray&&(f+=`[`+s[l].arraySize+`]`,p+=`v`),c.push(f),t._uniformList.push(l),u.ignore||((a===`sampler2D`||a===`samplerCube`)&&(t.textures[l]={shaderType:n,type:a}),d?t._addSemanticUniform(l,p,d):t._addMaterialUniform(l,a,p,m,s[l].isArray,e))}return c.length>0?`uniform `+a+` `+c.join(`,`)+`;
`:``}this.uniformTemplates=e},_parseAttributes:function(){var e={},t=this;this._vertexCode=this._vertexCode.replace(Yt,n);function n(n,r,i){var a=un(r,i),o=rn[r]||1,s=[];for(var c in a){var l=a[c].semantic;if(e[c]={type:`float`,size:o,semantic:l||null},l){if(en.indexOf(l)<0)throw Error(`Unkown semantic "`+l+`"`);t.attributeSemantics[l]={symbol:c,type:r}}s.push(c)}return`attribute `+r+` `+s.join(`,`)+`;
`}this.attributes=e},_parseDefines:function(){var e=this,t=`vertex`;this._vertexCode=this._vertexCode.replace(Xt,n),t=`fragment`,this._fragmentCode=this._fragmentCode.replace(Xt,n);function n(n,r,i){var a=t===`vertex`?e.vertexDefines:e.fragmentDefines;return a[r]||(i===`false`?a[r]=!1:i===`true`?a[r]=!0:a[r]=i?isNaN(parseFloat(i))?i.trim():parseFloat(i):null),``}},clone:function(){var e=on[this._shaderID];return new K(e.vertex,e.fragment)}},Object.defineProperty&&(Object.defineProperty(K.prototype,"shaderID",{get:function(){return this._shaderID}}),Object.defineProperty(K.prototype,"vertex",{get:function(){return this._vertexCode}}),Object.defineProperty(K.prototype,"fragment",{get:function(){return this._fragmentCode}}),Object.defineProperty(K.prototype,"uniforms",{get:function(){return this._uniformList}}));var dn=/(@import)\s*([0-9a-zA-Z_\-\.]*)/g;K.parseImport=function(e){return e=e.replace(dn,function(e,t,n){var e=K.source(n);return e?K.parseImport(e):(console.error(`Shader chunk "`+n+`" not existed in library`),``)}),e};var fn=/(@export)\s*([0-9a-zA-Z_\-\.]*)\s*\n([\s\S]*?)@end/g;K.import=function(e){e.replace(fn,function(e,t,n,r){var r=r.replace(/(^[\s\t\xa0\u3000]+)|([\u3000\xa0\s\t]+\x24)/g,``);if(r){for(var i=n.split(`.`),a=K.codes,o=0,s;o<i.length-1;)s=i[o++],a[s]||(a[s]={}),a=a[s];s=i[o],a[s]=r}return r})},K.codes={},K.source=function(e){for(var t=e.split(`.`),n=K.codes,r=0;n&&r<t.length;){var i=t[r++];n=n[i]}return typeof n==`string`?n:(console.error(`Shader "`+e+`" not existed in library`),``)};var pn=`@export clay.prez.vertex
uniform mat4 WVP : WORLDVIEWPROJECTION;
attribute vec3 pos : POSITION;
attribute vec2 uv : TEXCOORD_0;
uniform vec2 uvRepeat : [1.0, 1.0];
uniform vec2 uvOffset : [0.0, 0.0];
@import clay.chunk.skinning_header
@import clay.chunk.instancing_header
varying vec2 v_Texcoord;
void main()
{
 vec4 P = vec4(pos, 1.0);
#ifdef SKINNING
 @import clay.chunk.skin_matrix
 P = skinMatrixWS * P;
#endif
#ifdef INSTANCING
 @import clay.chunk.instancing_matrix
 P = instanceMat * P;
#endif
 gl_Position = WVP * P;
 v_Texcoord = uv * uvRepeat + uvOffset;
}
@end
@export clay.prez.fragment
uniform sampler2D alphaMap;
uniform float alphaCutoff: 0.0;
varying vec2 v_Texcoord;
void main()
{
 if (alphaCutoff > 0.0) {
 if (texture2D(alphaMap, v_Texcoord).a <= alphaCutoff) {
 discard;
 }
 }
 gl_FragColor = vec4(0.0,0.0,0.0,1.0);
}
@end`;K.import(pn);var mn=V.create,hn={};function gn(e){return e.material}function _n(e,t,n){return t.uniforms[n].value}function vn(e,t,n,r){return n!==r}function yn(e){return!0}function bn(){}var xn={float:U.FLOAT,byte:U.BYTE,ubyte:U.UNSIGNED_BYTE,short:U.SHORT,ushort:U.UNSIGNED_SHORT};function Sn(e,t,n){this.availableAttributes=e,this.availableAttributeSymbols=t,this.indicesBuffer=n,this.vao=null}function Cn(e){var t,n;this.bind=function(e){t||(t=ct.createCanvas(),t.width=t.height=1,t.getContext(`2d`));var r=e.gl,i=!n;i&&(n=r.createTexture()),r.bindTexture(r.TEXTURE_2D,n),i&&r.texImage2D(r.TEXTURE_2D,0,r.RGBA,r.RGBA,r.UNSIGNED_BYTE,t)},this.unbind=function(e){e.gl.bindTexture(e.gl.TEXTURE_2D,null)},this.isRenderable=function(){return!0}}var wn=Fe.extend(function(){return{canvas:null,_width:100,_height:100,devicePixelRatio:typeof window<`u`&&window.devicePixelRatio||1,clearColor:[0,0,0,0],clearBit:17664,alpha:!0,depth:!0,stencil:!1,antialias:!0,premultipliedAlpha:!0,preserveDrawingBuffer:!1,throwError:!0,gl:null,viewport:{},maxJointNumber:20,__currentFrameBuffer:null,_viewportStack:[],_clearStack:[],_sceneRendering:null}},function(){this.canvas||(this.canvas=ct.createCanvas());var e=this.canvas;try{var t={alpha:this.alpha,depth:this.depth,stencil:this.stencil,antialias:this.antialias,premultipliedAlpha:this.premultipliedAlpha,preserveDrawingBuffer:this.preserveDrawingBuffer};if(this.gl=e.getContext(`webgl`,t)||e.getContext(`experimental-webgl`,t),!this.gl)throw Error();this._glinfo=new it(this.gl),this.gl.targetRenderer&&console.error(`Already created a renderer`),this.gl.targetRenderer=this,this.resize()}catch(e){throw`Error creating WebGL Context `+e}this._programMgr=new qt(this),this._placeholderTexture=new Cn(this)},{resize:function(e,t){var n=this.canvas,r=this.devicePixelRatio;e==null?(this._width=n.width/r,this._height=n.height/r):(n.style&&(n.style.width=e+`px`,n.style.height=t+`px`),n.width=e*r,n.height=t*r,this._width=e,this._height=t),this.setViewport(0,0,this._width,this._height)},getWidth:function(){return this._width},getHeight:function(){return this._height},getViewportAspect:function(){var e=this.viewport;return e.width/e.height},setDevicePixelRatio:function(e){this.devicePixelRatio=e,this.resize(this._width,this._height)},getDevicePixelRatio:function(){return this.devicePixelRatio},getGLExtension:function(e){return this._glinfo.getExtension(e)},getGLParameter:function(e){return this._glinfo.getParameter(e)},setViewport:function(e,t,n,r,i){if(typeof e==`object`){var a=e;e=a.x,t=a.y,n=a.width,r=a.height,i=a.devicePixelRatio}i=i||this.devicePixelRatio,this.gl.viewport(e*i,t*i,n*i,r*i),this.viewport={x:e,y:t,width:n,height:r,devicePixelRatio:i}},saveViewport:function(){this._viewportStack.push(this.viewport)},restoreViewport:function(){this._viewportStack.length>0&&this.setViewport(this._viewportStack.pop())},saveClear:function(){this._clearStack.push({clearBit:this.clearBit,clearColor:this.clearColor})},restoreClear:function(){if(this._clearStack.length>0){var e=this._clearStack.pop();this.clearColor=e.clearColor,this.clearBit=e.clearBit}},bindSceneRendering:function(e){this._sceneRendering=e},render:function(e,t,n,r){var i=this.gl,a=this.clearColor;if(this.clearBit){i.colorMask(!0,!0,!0,!0),i.depthMask(!0);var o=this.viewport,s=!1,c=o.devicePixelRatio;(o.width!==this._width||o.height!==this._height||c&&c!==this.devicePixelRatio||o.x||o.y)&&(s=!0,i.enable(i.SCISSOR_TEST),i.scissor(o.x*c,o.y*c,o.width*c,o.height*c)),i.clearColor(a[0],a[1],a[2],a[3]),i.clear(this.clearBit),s&&i.disable(i.SCISSOR_TEST)}if(n||e.update(!1),e.updateLights(),t=t||e.getMainCamera(),!t){console.error(`Can't find camera in the scene.`);return}t.update();var l=e.updateRenderList(t,!0);this._sceneRendering=e;var u=l.opaque,d=l.transparent,f=e.material;e.trigger(`beforerender`,this,e,t,l),r?(this.renderPreZ(u,e,t),i.depthFunc(i.LEQUAL)):i.depthFunc(i.LESS);for(var p=mn(),m=I.create(),h=0;h<d.length;h++){var g=d[h];V.multiplyAffine(p,t.viewMatrix.array,g.worldTransform.array),I.transformMat4(m,g.position.array,p),g.__depth=m[2]}this.renderPass(u,t,{getMaterial:function(e){return f||e.material},sortCompare:this.opaqueSortCompare}),this.renderPass(d,t,{getMaterial:function(e){return f||e.material},sortCompare:this.transparentSortCompare}),e.trigger(`afterrender`,this,e,t,l),this._sceneRendering=null},getProgram:function(e,t,n){return t=t||e.material,this._programMgr.getProgram(e,t,n)},validateProgram:function(e){if(e.__error){var t=e.__error;if(hn[e.__uid__])return;if(hn[e.__uid__]=!0,this.throwError)throw Error(t);this.trigger(`error`,t)}},updatePrograms:function(e,t,n){var r=n&&n.getMaterial||gn;t=t||null;for(var i=0;i<e.length;i++){var a=e[i],o=r.call(this,a);if(i>0){var s=e[i-1],c=s.joints?s.joints.length:0;if((a.joints?a.joints.length:0)===c&&a.material===s.material&&a.lightGroup===s.lightGroup){a.__program=s.__program;continue}}var l=this._programMgr.getProgram(a,o,t);this.validateProgram(l),a.__program=l}},renderPass:function(e,t,n){this.trigger(`beforerenderpass`,this,e,t,n),n=n||{},n.getMaterial=n.getMaterial||gn,n.getUniform=n.getUniform||_n,n.isMaterialChanged=n.isMaterialChanged||vn,n.beforeRender=n.beforeRender||bn,n.afterRender=n.afterRender||bn;var r=n.ifRender||yn;this.updatePrograms(e,this._sceneRendering,n),n.sortCompare&&e.sort(n.sortCompare);var i=this.viewport,a=i.devicePixelRatio,o=[i.x*a,i.y*a,i.width*a,i.height*a],s=this.devicePixelRatio,c=this.__currentFrameBuffer?[this.__currentFrameBuffer.getTextureWidth(),this.__currentFrameBuffer.getTextureHeight()]:[this._width*s,this._height*s],l=[o[2],o[3]],u=Date.now();t?(V.copy(Tn.VIEW,t.viewMatrix.array),V.copy(Tn.PROJECTION,t.projectionMatrix.array),V.copy(Tn.VIEWINVERSE,t.worldTransform.array)):(V.identity(Tn.VIEW),V.identity(Tn.PROJECTION),V.identity(Tn.VIEWINVERSE)),V.multiply(Tn.VIEWPROJECTION,Tn.PROJECTION,Tn.VIEW),V.invert(Tn.PROJECTIONINVERSE,Tn.PROJECTION),V.invert(Tn.VIEWPROJECTIONINVERSE,Tn.VIEWPROJECTION);for(var d=this.gl,f=this._sceneRendering,p,m,h,g,_,v,y,b,x,S,C,w,T=null,E=0;E<e.length;E++){var D=e[E],O=D.worldTransform!=null,k;if(r(D)){O&&(k=D.isSkinnedMesh&&D.isSkinnedMesh()?D.offsetMatrix?D.offsetMatrix.array:Tn.IDENTITY:D.worldTransform.array);var A=D.geometry,j=n.getMaterial.call(this,D),M=D.__program,N=j.shader,ee=A.__uid__+`-`+M.__uid__,te=ee!==S;S=ee,O&&(V.copy(Tn.WORLD,k),V.multiply(Tn.WORLDVIEWPROJECTION,Tn.VIEWPROJECTION,k),V.multiplyAffine(Tn.WORLDVIEW,Tn.VIEW,k),(N.matrixSemantics.WORLDINVERSE||N.matrixSemantics.WORLDINVERSETRANSPOSE)&&V.invert(Tn.WORLDINVERSE,k),(N.matrixSemantics.WORLDVIEWINVERSE||N.matrixSemantics.WORLDVIEWINVERSETRANSPOSE)&&V.invert(Tn.WORLDVIEWINVERSE,Tn.WORLDVIEW),(N.matrixSemantics.WORLDVIEWPROJECTIONINVERSE||N.matrixSemantics.WORLDVIEWPROJECTIONINVERSETRANSPOSE)&&V.invert(Tn.WORLDVIEWPROJECTIONINVERSE,Tn.WORLDVIEWPROJECTION)),D.beforeRender&&D.beforeRender(this),n.beforeRender.call(this,D,j,p);var P=M!==m;P?(M.bind(this),M.setUniformOfSemantic(d,`VIEWPORT`,o),M.setUniformOfSemantic(d,`WINDOW_SIZE`,c),t&&(M.setUniformOfSemantic(d,`NEAR`,t.near),M.setUniformOfSemantic(d,`FAR`,t.far)),M.setUniformOfSemantic(d,`DEVICEPIXELRATIO`,a),M.setUniformOfSemantic(d,`TIME`,u),M.setUniformOfSemantic(d,`VIEWPORT_SIZE`,l),f&&f.setLightUniforms(M,D.lightGroup,this)):M=m,(P||n.isMaterialChanged(D,h,j,p))&&(j.depthTest!==g&&(j.depthTest?d.enable(d.DEPTH_TEST):d.disable(d.DEPTH_TEST),g=j.depthTest),j.depthMask!==_&&(d.depthMask(j.depthMask),_=j.depthMask),j.transparent!==x&&(j.transparent?d.enable(d.BLEND):d.disable(d.BLEND),x=j.transparent),j.transparent&&(j.blend?j.blend(d):(d.blendEquationSeparate(d.FUNC_ADD,d.FUNC_ADD),d.blendFuncSeparate(d.SRC_ALPHA,d.ONE_MINUS_SRC_ALPHA,d.ONE,d.ONE_MINUS_SRC_ALPHA))),w=this._bindMaterial(D,j,M,h||null,p||null,m||null,n.getUniform),p=j);var ne=N.matrixSemanticKeys;if(O)for(var re=0;re<ne.length;re++){var ie=ne[re],ae=N.matrixSemantics[ie],F=Tn[ie];if(ae.isTranspose){var oe=Tn[ae.semanticNoTranspose];V.transpose(F,oe)}M.setUniform(d,ae.type,ae.symbol,F)}D.cullFace!==y&&(y=D.cullFace,d.cullFace(y)),D.frontFace!==b&&(b=D.frontFace,d.frontFace(b)),D.culling!==v&&(v=D.culling,v?d.enable(d.CULL_FACE):d.disable(d.CULL_FACE)),this._updateSkeleton(D,M,w),te&&(C=this._bindVAO(T,N,A,M)),this._renderObject(D,C,M),n.afterRender(this,D),D.afterRender&&D.afterRender(this),m=M,h=D}}this.trigger(`afterrenderpass`,this,e,t,n)},getMaxJointNumber:function(){return this.maxJointNumber},_updateSkeleton:function(e,t,n){var r=this.gl,i=e.skeleton;if(i)if(i.update(),e.joints.length>this.getMaxJointNumber()){var a=i.getSubSkinMatricesTexture(e.__uid__,e.joints);t.useTextureSlot(this,a,n),t.setUniform(r,`1i`,`skinMatricesTexture`,n),t.setUniform(r,`1f`,`skinMatricesTextureSize`,a.width)}else{var o=i.getSubSkinMatrices(e.__uid__,e.joints);t.setUniformOfSemantic(r,`SKIN_MATRIX`,o)}},_renderObject:function(e,t,n){var r=this.gl,i=e.geometry,a=e.mode;a==null&&(a=4);var o=null,s=e.isInstancedMesh&&e.isInstancedMesh();if(s&&(o=this.getGLExtension(`ANGLE_instanced_arrays`),!o)){console.warn(`Device not support ANGLE_instanced_arrays extension`);return}var c;if(s&&(c=this._bindInstancedAttributes(e,n,o)),t.indicesBuffer){var l=this.getGLExtension(`OES_element_index_uint`)&&i.indices instanceof Uint32Array?r.UNSIGNED_INT:r.UNSIGNED_SHORT;s?o.drawElementsInstancedANGLE(a,t.indicesBuffer.count,l,0,e.getInstanceCount()):r.drawElements(a,t.indicesBuffer.count,l,0)}else s?o.drawArraysInstancedANGLE(a,0,i.vertexCount,e.getInstanceCount()):r.drawArrays(a,0,i.vertexCount);if(s)for(var u=0;u<c.length;u++)r.disableVertexAttribArray(c[u])},_bindInstancedAttributes:function(e,t,n){for(var r=this.gl,i=e.getInstancedAttributesBuffers(this),a=[],o=0;o<i.length;o++){var s=i[o],c=t.getAttribLocation(r,s.symbol);if(!(c<0)){var l=xn[s.type]||r.FLOAT;r.enableVertexAttribArray(c),r.bindBuffer(r.ARRAY_BUFFER,s.buffer),r.vertexAttribPointer(c,s.size,l,!1,0,0),n.vertexAttribDivisorANGLE(c,s.divisor),a.push(c)}}return a},_bindMaterial:function(e,t,n,r,i,a,o){for(var s=this.gl,c=a===n,l=n.currentTextureSlot(),u=t.getEnabledUniforms(),d=t.getTextureUniforms(),f=this._placeholderTexture,p=0;p<d.length;p++){var m=d[p],h=o(e,t,m),g=t.uniforms[m].type;if(g===`t`&&h)h.__slot=-1;else if(g===`tv`)for(var _=0;_<h.length;_++)h[_]&&(h[_].__slot=-1)}f.__slot=-1;for(var p=0;p<u.length;p++){var m=u[p],v=t.uniforms[m],h=o(e,t,m),g=v.type,y=g===`t`;if(y&&(!h||!h.isRenderable())&&(h=f),i&&c){var b=o(r,i,m);if(y&&(!b||!b.isRenderable())&&(b=f),b===h){if(y)n.takeCurrentTextureSlot(this,null);else if(g===`tv`&&h)for(var _=0;_<h.length;_++)n.takeCurrentTextureSlot(this,null);continue}}if(h!=null)if(y)if(h.__slot<0){var x=n.currentTextureSlot();n.setUniform(s,`1i`,m,x)&&(n.takeCurrentTextureSlot(this,h),h.__slot=x)}else n.setUniform(s,`1i`,m,h.__slot);else if(Array.isArray(h)){if(h.length===0)continue;if(g===`tv`){if(!n.hasUniform(m))continue;for(var S=[],_=0;_<h.length;_++){var C=h[_];if(C.__slot<0){var x=n.currentTextureSlot();S.push(x),n.takeCurrentTextureSlot(this,C),C.__slot=x}else S.push(C.__slot)}n.setUniform(s,`1iv`,m,S)}else n.setUniform(s,v.type,m,h)}else n.setUniform(s,v.type,m,h)}var w=n.currentTextureSlot();return n.resetTextureSlot(l),w},_bindVAO:function(e,t,n,r){var i=!n.dynamic,a=this.gl,o=this.__uid__+`-`+r.__uid__,s=n.__vaoCache[o];if(!s){var c=n.getBufferChunks(this);if(!c||!c.length)return;for(var l=c[0],u=l.attributeBuffers,d=l.indicesBuffer,f=[],p=[],m=0;m<u.length;m++){var h=u[m],g=h.name,_=h.semantic,v;if(_){var y=t.attributeSemantics[_];v=y&&y.symbol}else v=g;v&&r.attributes[v]&&(f.push(h),p.push(v))}s=new Sn(f,p,d),i&&(n.__vaoCache[o]=s)}var b=!0;e&&i&&(s.vao==null?s.vao=e.createVertexArrayOES():b=!1,e.bindVertexArrayOES(s.vao));var f=s.availableAttributes,d=s.indicesBuffer;if(b){for(var x=r.enableAttributes(this,s.availableAttributeSymbols,e&&i&&s),m=0;m<f.length;m++){var S=x[m];if(S!==-1){var h=f[m],C=h.buffer,w=h.size,T=xn[h.type]||a.FLOAT;a.bindBuffer(a.ARRAY_BUFFER,C),a.vertexAttribPointer(S,w,T,!1,0,0)}}n.isUseIndices()&&a.bindBuffer(a.ELEMENT_ARRAY_BUFFER,d.buffer)}return s},renderPreZ:function(e,t,n){var r=this.gl,i=this._prezMaterial||new Mt({shader:new K(K.source(`clay.prez.vertex`),K.source(`clay.prez.fragment`))});this._prezMaterial=i,r.colorMask(!1,!1,!1,!1),r.depthMask(!0),this.renderPass(e,n,{ifRender:function(e){return!e.ignorePreZ},isMaterialChanged:function(e,t){var n=e.material,r=t.material;return n.get(`diffuseMap`)!==r.get(`diffuseMap`)||(n.get(`alphaCutoff`)||0)!==(r.get(`alphaCutoff`)||0)},getUniform:function(e,t,n){return n===`alphaMap`?e.material.get(`diffuseMap`):n===`alphaCutoff`?e.material.isDefined(`fragment`,`ALPHA_TEST`)&&e.material.get(`diffuseMap`)&&e.material.get(`alphaCutoff`)||0:n===`uvRepeat`?e.material.get(`uvRepeat`):n===`uvOffset`?e.material.get(`uvOffset`):t.get(n)},getMaterial:function(){return i},sort:this.opaqueSortCompare}),r.colorMask(!0,!0,!0,!0),r.depthMask(!0)},disposeScene:function(e){this.disposeNode(e,!0,!0),e.dispose()},disposeNode:function(e,t,n){e.getParent()&&e.getParent().remove(e);var r={};e.traverse(function(e){var i=e.material;if(e.geometry&&t&&e.geometry.dispose(this),n&&i&&!r[i.__uid__]){for(var a=i.getTextureUniforms(),o=0;o<a.length;o++){var s=a[o],c=i.uniforms[s].value,l=i.uniforms[s].type;if(c){if(l===`t`)c.dispose&&c.dispose(this);else if(l===`tv`)for(var u=0;u<c.length;u++)c[u]&&c[u].dispose&&c[u].dispose(this)}}r[i.__uid__]=!0}e.dispose&&e.dispose(this)},this)},disposeGeometry:function(e){e.dispose(this)},disposeTexture:function(e){e.dispose(this)},disposeFrameBuffer:function(e){e.dispose(this)},dispose:function(){},screenToNDC:function(e,t,n){n||(n=new G),t=this._height-t;var r=this.viewport,i=n.array;return i[0]=(e-r.x)/r.width,i[0]=i[0]*2-1,i[1]=(t-r.y)/r.height,i[1]=i[1]*2-1,n}});wn.opaqueSortCompare=wn.prototype.opaqueSortCompare=function(e,t){return e.renderOrder===t.renderOrder?e.__program===t.__program?e.material===t.material?e.geometry.__uid__-t.geometry.__uid__:e.material.__uid__-t.material.__uid__:e.__program&&t.__program?e.__program.__uid__-t.__program.__uid__:0:e.renderOrder-t.renderOrder},wn.transparentSortCompare=wn.prototype.transparentSortCompare=function(e,t){return e.renderOrder===t.renderOrder?e.__depth===t.__depth?e.__program===t.__program?e.material===t.material?e.geometry.__uid__-t.geometry.__uid__:e.material.__uid__-t.material.__uid__:e.__program&&t.__program?e.__program.__uid__-t.__program.__uid__:0:e.__depth-t.__depth:e.renderOrder-t.renderOrder};var Tn={IDENTITY:mn(),WORLD:mn(),VIEW:mn(),PROJECTION:mn(),WORLDVIEW:mn(),VIEWPROJECTION:mn(),WORLDVIEWPROJECTION:mn(),WORLDINVERSE:mn(),VIEWINVERSE:mn(),PROJECTIONINVERSE:mn(),WORLDVIEWINVERSE:mn(),VIEWPROJECTIONINVERSE:mn(),WORLDVIEWPROJECTIONINVERSE:mn(),WORLDTRANSPOSE:mn(),VIEWTRANSPOSE:mn(),PROJECTIONTRANSPOSE:mn(),WORLDVIEWTRANSPOSE:mn(),VIEWPROJECTIONTRANSPOSE:mn(),WORLDVIEWPROJECTIONTRANSPOSE:mn(),WORLDINVERSETRANSPOSE:mn(),VIEWINVERSETRANSPOSE:mn(),PROJECTIONINVERSETRANSPOSE:mn(),WORLDVIEWINVERSETRANSPOSE:mn(),VIEWPROJECTIONINVERSETRANSPOSE:mn(),WORLDVIEWPROJECTIONINVERSETRANSPOSE:mn()};wn.COLOR_BUFFER_BIT=U.COLOR_BUFFER_BIT,wn.DEPTH_BUFFER_BIT=U.DEPTH_BUFFER_BIT,wn.STENCIL_BUFFER_BIT=U.STENCIL_BUFFER_BIT;var En=`__dt__`,Dn=function(){this._contextId=0,this._caches=[],this._context={}};Dn.prototype={use:function(e,t){var n=this._caches;n[e]||(n[e]={},t&&(n[e]=t())),this._contextId=e,this._context=n[e]},put:function(e,t){this._context[e]=t},get:function(e){return this._context[e]},dirty:function(e){e=e||``;var t=En+e;this.put(t,!0)},dirtyAll:function(e){e=e||``;for(var t=En+e,n=this._caches,r=0;r<n.length;r++)n[r]&&(n[r][t]=!0)},fresh:function(e){e=e||``;var t=En+e;this.put(t,!1)},freshAll:function(e){e=e||``;for(var t=En+e,n=this._caches,r=0;r<n.length;r++)n[r]&&(n[r][t]=!1)},isDirty:function(e){e=e||``;var t=En+e,n=this._context;return!n.hasOwnProperty(t)||n[t]===!0},deleteContext:function(e){delete this._caches[e],this._context={}},delete:function(e){delete this._context[e]},clearAll:function(){this._caches={}},getContext:function(){return this._context},eachContext:function(e,t){Object.keys(this._caches).forEach(function(n){e&&e.call(t,n)})},miss:function(e){return!this._context.hasOwnProperty(e)}},Dn.prototype.constructor=Dn;var q=Fe.extend({width:512,height:512,type:U.UNSIGNED_BYTE,format:U.RGBA,wrapS:U.REPEAT,wrapT:U.REPEAT,minFilter:U.LINEAR_MIPMAP_LINEAR,magFilter:U.LINEAR,useMipmap:!0,anisotropic:1,flipY:!0,sRGB:!0,unpackAlignment:4,premultiplyAlpha:!1,dynamic:!1,NPOT:!1,__used:0},function(){this._cache=new Dn},{getWebGLTexture:function(e){var t=e.gl,n=this._cache;return n.use(e.__uid__),n.miss(`webgl_texture`)&&n.put(`webgl_texture`,t.createTexture()),this.dynamic?this.update(e):n.isDirty()&&(this.update(e),n.fresh()),n.get(`webgl_texture`)},bind:function(){},unbind:function(){},dirty:function(){this._cache&&this._cache.dirtyAll()},update:function(e){},updateCommon:function(e){var t=e.gl;t.pixelStorei(t.UNPACK_FLIP_Y_WEBGL,this.flipY),t.pixelStorei(t.UNPACK_PREMULTIPLY_ALPHA_WEBGL,this.premultiplyAlpha),t.pixelStorei(t.UNPACK_ALIGNMENT,this.unpackAlignment),this.format===U.DEPTH_COMPONENT&&(this.useMipmap=!1);var n=e.getGLExtension(`EXT_sRGB`);this.format===q.SRGB&&!n&&(this.format=q.RGB),this.format===q.SRGB_ALPHA&&!n&&(this.format=q.RGBA),this.NPOT=!this.isPowerOfTwo()},getAvailableWrapS:function(){return this.NPOT?U.CLAMP_TO_EDGE:this.wrapS},getAvailableWrapT:function(){return this.NPOT?U.CLAMP_TO_EDGE:this.wrapT},getAvailableMinFilter:function(){var e=this.minFilter;return this.NPOT||!this.useMipmap?e===U.NEAREST_MIPMAP_NEAREST||e===U.NEAREST_MIPMAP_LINEAR?U.NEAREST:e===U.LINEAR_MIPMAP_LINEAR||e===U.LINEAR_MIPMAP_NEAREST?U.LINEAR:e:e},getAvailableMagFilter:function(){return this.magFilter},nextHighestPowerOfTwo:function(e){--e;for(var t=1;t<32;t<<=1)e|=e>>t;return e+1},dispose:function(e){var t=this._cache;t.use(e.__uid__);var n=t.get(`webgl_texture`);n&&e.gl.deleteTexture(n),t.deleteContext(e.__uid__)},isRenderable:function(){},isPowerOfTwo:function(){}});Object.defineProperty(q.prototype,"width",{get:function(){return this._width},set:function(e){this._width=e}}),Object.defineProperty(q.prototype,"height",{get:function(){return this._height},set:function(e){this._height=e}}),q.BYTE=U.BYTE,q.UNSIGNED_BYTE=U.UNSIGNED_BYTE,q.SHORT=U.SHORT,q.UNSIGNED_SHORT=U.UNSIGNED_SHORT,q.INT=U.INT,q.UNSIGNED_INT=U.UNSIGNED_INT,q.FLOAT=U.FLOAT,q.HALF_FLOAT=36193,q.UNSIGNED_INT_24_8_WEBGL=34042,q.DEPTH_COMPONENT=U.DEPTH_COMPONENT,q.DEPTH_STENCIL=U.DEPTH_STENCIL,q.ALPHA=U.ALPHA,q.RGB=U.RGB,q.RGBA=U.RGBA,q.LUMINANCE=U.LUMINANCE,q.LUMINANCE_ALPHA=U.LUMINANCE_ALPHA,q.SRGB=35904,q.SRGB_ALPHA=35906,q.COMPRESSED_RGB_S3TC_DXT1_EXT=33776,q.COMPRESSED_RGBA_S3TC_DXT1_EXT=33777,q.COMPRESSED_RGBA_S3TC_DXT3_EXT=33778,q.COMPRESSED_RGBA_S3TC_DXT5_EXT=33779,q.NEAREST=U.NEAREST,q.LINEAR=U.LINEAR,q.NEAREST_MIPMAP_NEAREST=U.NEAREST_MIPMAP_NEAREST,q.LINEAR_MIPMAP_NEAREST=U.LINEAR_MIPMAP_NEAREST,q.NEAREST_MIPMAP_LINEAR=U.NEAREST_MIPMAP_LINEAR,q.LINEAR_MIPMAP_LINEAR=U.LINEAR_MIPMAP_LINEAR,q.REPEAT=U.REPEAT,q.CLAMP_TO_EDGE=U.CLAMP_TO_EDGE,q.MIRRORED_REPEAT=U.MIRRORED_REPEAT;var On={};On.isPowerOfTwo=function(e){return(e&e-1)==0},On.nextPowerOfTwo=function(e){return e--,e|=e>>1,e|=e>>2,e|=e>>4,e|=e>>8,e|=e>>16,e++,e},On.nearestPowerOfTwo=function(e){return 2**Math.round(Math.log(e)/Math.LN2)};var kn=On.isPowerOfTwo;function An(e){return 2**Math.round(Math.log(e)/Math.LN2)}function jn(e,t){var n=An(e.width),r=An(e.height);return t=t||document.createElement(`canvas`),t.width=n,t.height=r,t.getContext(`2d`).drawImage(e.image,0,0,n,r),t}var J=q.extend(function(){return{image:null,pixels:null,mipmaps:[],convertToPOT:!1}},{textureType:`texture2D`,update:function(e){var t=e.gl;t.bindTexture(t.TEXTURE_2D,this._cache.get(`webgl_texture`)),this.updateCommon(e);var n=this.format,r=this.type,i=!!(this.convertToPOT&&!this.mipmaps.length&&this.image&&(this.wrapS===q.REPEAT||this.wrapT===q.REPEAT)&&this.NPOT);t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_S,i?this.wrapS:this.getAvailableWrapS()),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_T,i?this.wrapT:this.getAvailableWrapT()),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MAG_FILTER,i?this.magFilter:this.getAvailableMagFilter()),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MIN_FILTER,i?this.minFilter:this.getAvailableMinFilter());var a=e.getGLExtension(`EXT_texture_filter_anisotropic`);if(a&&this.anisotropic>1&&t.texParameterf(t.TEXTURE_2D,a.TEXTURE_MAX_ANISOTROPY_EXT,this.anisotropic),r===36193&&(e.getGLExtension(`OES_texture_half_float`)||(r=U.FLOAT)),this.mipmaps.length)for(var o=this.width,s=this.height,c=0;c<this.mipmaps.length;c++){var l=this.mipmaps[c];this._updateTextureData(t,l,c,o,s,n,r,!1),o/=2,s/=2}else this._updateTextureData(t,this,0,this.width,this.height,n,r,i),this.useMipmap&&(!this.NPOT||i)&&t.generateMipmap(t.TEXTURE_2D);t.bindTexture(t.TEXTURE_2D,null)},_updateTextureData:function(e,t,n,r,i,a,o,s){if(t.image){var c=t.image;s&&(this._potCanvas=jn(this,this._potCanvas),c=this._potCanvas),e.texImage2D(e.TEXTURE_2D,n,a,a,o,c)}else a<=q.COMPRESSED_RGBA_S3TC_DXT5_EXT&&a>=q.COMPRESSED_RGB_S3TC_DXT1_EXT?e.compressedTexImage2D(e.TEXTURE_2D,n,a,r,i,0,t.pixels):e.texImage2D(e.TEXTURE_2D,n,a,r,i,0,a,o,t.pixels)},generateMipmap:function(e){var t=e.gl;this.useMipmap&&!this.NPOT&&(t.bindTexture(t.TEXTURE_2D,this._cache.get(`webgl_texture`)),t.generateMipmap(t.TEXTURE_2D))},isPowerOfTwo:function(){return kn(this.width)&&kn(this.height)},isRenderable:function(){return this.image?this.image.width>0&&this.image.height>0:!!(this.width&&this.height)},bind:function(e){e.gl.bindTexture(e.gl.TEXTURE_2D,this.getWebGLTexture(e))},unbind:function(e){e.gl.bindTexture(e.gl.TEXTURE_2D,null)},load:function(e,t){var n=ct.createImage();t&&(n.crossOrigin=t);var r=this;return n.onload=function(){r.dirty(),r.trigger(`success`,r)},n.onerror=function(){r.trigger(`error`,r)},n.src=e,this.image=n,this}});Object.defineProperty(J.prototype,"width",{get:function(){return this.image?this.image.width:this._width},set:function(e){this.image?console.warn(`Texture from image can't set width`):(this._width!==e&&this.dirty(),this._width=e)}}),Object.defineProperty(J.prototype,"height",{get:function(){return this.image?this.image.height:this._height},set:function(e){this.image?console.warn(`Texture from image can't set height`):(this._height!==e&&this.dirty(),this._height=e)}});function Mn(e){return{byte:ct.Int8Array,ubyte:ct.Uint8Array,short:ct.Int16Array,ushort:ct.Uint16Array}[e]||ct.Float32Array}function Nn(e){return`attr_`+e}function Pn(e,t,n,r){switch(this.name=e,this.type=t,this.size=n,this.semantic=r||``,this.value=null,n){case 1:this.get=function(e){return this.value[e]},this.set=function(e,t){this.value[e]=t},this.copy=function(e,t){this.value[e]=this.value[e]};break;case 2:this.get=function(e,t){var n=this.value;return t[0]=n[e*2],t[1]=n[e*2+1],t},this.set=function(e,t){var n=this.value;n[e*2]=t[0],n[e*2+1]=t[1]},this.copy=function(e,t){var n=this.value;t*=2,e*=2,n[e]=n[t],n[e+1]=n[t+1]};break;case 3:this.get=function(e,t){var n=e*3,r=this.value;return t[0]=r[n],t[1]=r[n+1],t[2]=r[n+2],t},this.set=function(e,t){var n=e*3,r=this.value;r[n]=t[0],r[n+1]=t[1],r[n+2]=t[2]},this.copy=function(e,t){var n=this.value;t*=3,e*=3,n[e]=n[t],n[e+1]=n[t+1],n[e+2]=n[t+2]};break;case 4:this.get=function(e,t){var n=this.value,r=e*4;return t[0]=n[r],t[1]=n[r+1],t[2]=n[r+2],t[3]=n[r+3],t},this.set=function(e,t){var n=this.value,r=e*4;n[r]=t[0],n[r+1]=t[1],n[r+2]=t[2],n[r+3]=t[3]},this.copy=function(e,t){var n=this.value;t*=4,e*=4,n[e]=n[t],n[e+1]=n[t+1],n[e+2]=n[t+2],n[e+3]=n[t+3]}}}Pn.prototype.init=function(e){if(!this.value||this.value.length!==e*this.size){var t=Mn(this.type);this.value=new t(e*this.size)}},Pn.prototype.fromArray=function(e){var t=Mn(this.type),n;if(e[0]&&e[0].length){var r=0,i=this.size;n=new t(e.length*i);for(var a=0;a<e.length;a++)for(var o=0;o<i;o++)n[r++]=e[a][o]}else n=new t(e);this.value=n},Pn.prototype.clone=function(e){var t=new Pn(this.name,this.type,this.size,this.semantic);return e&&console.warn(`todo`),t};function Fn(e,t,n,r,i){this.name=e,this.type=t,this.buffer=n,this.size=r,this.semantic=i,this.symbol=``,this.needsRemove=!1}function In(e){this.buffer=e,this.count=0}var Ln=Fe.extend(function(){return{attributes:{},indices:null,dynamic:!0,_enabledAttributes:null,__used:0}},function(){this._cache=new Dn,this._attributeList=Object.keys(this.attributes),this.__vaoCache={}},{mainAttribute:``,pick:null,pickByRay:null,dirty:function(){for(var e=this.getEnabledAttributes(),t=0;t<e.length;t++)this.dirtyAttribute(e[t]);this.dirtyIndices(),this._enabledAttributes=null,this._cache.dirty(`any`)},dirtyIndices:function(){this._cache.dirtyAll(`indices`)},dirtyAttribute:function(e){this._cache.dirtyAll(Nn(e)),this._cache.dirtyAll(`attributes`)},getTriangleIndices:function(e,t){if(e<this.triangleCount&&e>=0){t||(t=[]);var n=this.indices;return t[0]=n[e*3],t[1]=n[e*3+1],t[2]=n[e*3+2],t}},setTriangleIndices:function(e,t){var n=this.indices;n[e*3]=t[0],n[e*3+1]=t[1],n[e*3+2]=t[2]},isUseIndices:function(){return!!this.indices},initIndicesFromArray:function(e){var t,n=this.vertexCount>65535?ct.Uint32Array:ct.Uint16Array;if(e[0]&&e[0].length){var r=0,i=3;t=new n(e.length*i);for(var a=0;a<e.length;a++)for(var o=0;o<i;o++)t[r++]=e[a][o]}else t=new n(e);this.indices=t},createAttribute:function(e,t,n,r){var i=new Pn(e,t,n,r);return this.attributes[e]&&this.removeAttribute(e),this.attributes[e]=i,this._attributeList.push(e),i},removeAttribute:function(e){var t=this._attributeList,n=t.indexOf(e);return n>=0?(t.splice(n,1),delete this.attributes[e],!0):!1},getAttribute:function(e){return this.attributes[e]},getEnabledAttributes:function(){var e=this._enabledAttributes,t=this._attributeList;if(e)return e;for(var n=[],r=this.vertexCount,i=0;i<t.length;i++){var a=t[i],o=this.attributes[a];o.value&&o.value.length===r*o.size&&n.push(a)}return this._enabledAttributes=n,n},getBufferChunks:function(e){var t=this._cache;t.use(e.__uid__);var n=t.isDirty(`attributes`),r=t.isDirty(`indices`);if(n||r){this._updateBuffer(e.gl,n,r);for(var i=this.getEnabledAttributes(),a=0;a<i.length;a++)t.fresh(Nn(i[a]));t.fresh(`attributes`),t.fresh(`indices`)}return t.fresh(`any`),t.get(`chunks`)},_updateBuffer:function(e,t,n){var r=this._cache,i=r.get(`chunks`),a=!1;i||(i=[],i[0]={attributeBuffers:[],indicesBuffer:null},r.put(`chunks`,i),a=!0);var o=i[0],s=o.attributeBuffers,c=o.indicesBuffer;if(t||a){var l=this.getEnabledAttributes(),u={};if(!a)for(var d=0;d<s.length;d++)u[s[d].name]=s[d];for(var f=0;f<l.length;f++){var p=l[f],m=this.attributes[p],h;a||(h=u[p]);var g=h?h.buffer:e.createBuffer();r.isDirty(Nn(p))&&(e.bindBuffer(e.ARRAY_BUFFER,g),e.bufferData(e.ARRAY_BUFFER,m.value,this.dynamic?e.DYNAMIC_DRAW:e.STATIC_DRAW)),s[f]=new Fn(p,m.type,g,m.size,m.semantic)}for(var d=f;d<s.length;d++)e.deleteBuffer(s[d].buffer);s.length=f}this.isUseIndices()&&(n||a)&&(c||(c=new In(e.createBuffer()),o.indicesBuffer=c),c.count=this.indices.length,e.bindBuffer(e.ELEMENT_ARRAY_BUFFER,c.buffer),e.bufferData(e.ELEMENT_ARRAY_BUFFER,this.indices,this.dynamic?e.DYNAMIC_DRAW:e.STATIC_DRAW))},dispose:function(e){var t=this._cache;t.use(e.__uid__);var n=t.get(`chunks`);if(n)for(var r=0;r<n.length;r++){for(var i=n[r],a=0;a<i.attributeBuffers.length;a++){var o=i.attributeBuffers[a];e.gl.deleteBuffer(o.buffer)}i.indicesBuffer&&e.gl.deleteBuffer(i.indicesBuffer.buffer)}if(this.__vaoCache){var s=e.getGLExtension(`OES_vertex_array_object`);for(var c in this.__vaoCache){var l=this.__vaoCache[c].vao;l&&s.deleteVertexArrayOES(l)}}this.__vaoCache={},t.deleteContext(e.__uid__)}});Object.defineProperty&&(Object.defineProperty(Ln.prototype,"vertexCount",{enumerable:!1,get:function(){var e=this.attributes[this.mainAttribute];return e||(e=this.attributes[this._attributeList[0]]),!e||!e.value?0:e.value.length/e.size}}),Object.defineProperty(Ln.prototype,"triangleCount",{enumerable:!1,get:function(){var e=this.indices;return e?e.length/3:0}})),Ln.STATIC_DRAW=U.STATIC_DRAW,Ln.DYNAMIC_DRAW=U.DYNAMIC_DRAW,Ln.STREAM_DRAW=U.STREAM_DRAW,Ln.AttributeBuffer=Fn,Ln.IndicesBuffer=In,Ln.Attribute=Pn;var Rn=I.create,zn=I.add,Bn=I.set,Vn=Ln.Attribute,Y=Ln.extend(function(){return{attributes:{position:new Vn(`position`,`float`,3,`POSITION`),texcoord0:new Vn(`texcoord0`,`float`,2,`TEXCOORD_0`),texcoord1:new Vn(`texcoord1`,`float`,2,`TEXCOORD_1`),normal:new Vn(`normal`,`float`,3,`NORMAL`),tangent:new Vn(`tangent`,`float`,4,`TANGENT`),color:new Vn(`color`,`float`,4,`COLOR`),weight:new Vn(`weight`,`float`,3,`WEIGHT`),joint:new Vn(`joint`,`float`,4,`JOINT`),barycentric:new Vn(`barycentric`,`float`,3,null)},boundingBox:null}},{mainAttribute:`position`,updateBoundingBox:function(){var e=this.boundingBox;e||(e=this.boundingBox=new Ze);var t=this.attributes.position.value;if(t&&t.length){var n=e.min,r=e.max,i=n.array,a=r.array;I.set(i,t[0],t[1],t[2]),I.set(a,t[0],t[1],t[2]);for(var o=3;o<t.length;){var s=t[o++],c=t[o++],l=t[o++];s<i[0]&&(i[0]=s),c<i[1]&&(i[1]=c),l<i[2]&&(i[2]=l),s>a[0]&&(a[0]=s),c>a[1]&&(a[1]=c),l>a[2]&&(a[2]=l)}n._dirty=!0,r._dirty=!0}},generateVertexNormals:function(){if(this.vertexCount){var e=this.indices,t=this.attributes,n=t.position.value,r=t.normal.value;if(!r||r.length!==n.length)r=t.normal.value=new ct.Float32Array(n.length);else for(var i=0;i<r.length;i++)r[i]=0;for(var a=Rn(),o=Rn(),s=Rn(),c=Rn(),l=Rn(),u=Rn(),d=e?e.length:this.vertexCount,f,p,m,h=0;h<d;){e?(f=e[h++],p=e[h++],m=e[h++]):(f=h++,p=h++,m=h++),Bn(a,n[f*3],n[f*3+1],n[f*3+2]),Bn(o,n[p*3],n[p*3+1],n[p*3+2]),Bn(s,n[m*3],n[m*3+1],n[m*3+2]),I.sub(c,a,o),I.sub(l,o,s),I.cross(u,c,l);for(var i=0;i<3;i++)r[f*3+i]=r[f*3+i]+u[i],r[p*3+i]=r[p*3+i]+u[i],r[m*3+i]=r[m*3+i]+u[i]}for(var i=0;i<r.length;)Bn(u,r[i],r[i+1],r[i+2]),I.normalize(u,u),r[i++]=u[0],r[i++]=u[1],r[i++]=u[2];this.dirty()}},generateFaceNormals:function(){if(this.vertexCount){this.isUniqueVertex()||this.generateUniqueVertex();var e=this.indices,t=this.attributes,n=t.position.value,r=t.normal.value,i=Rn(),a=Rn(),o=Rn(),s=Rn(),c=Rn(),l=Rn();r||(r=t.normal.value=new Float32Array(n.length));for(var u=e?e.length:this.vertexCount,d,f,p,m=0;m<u;){e?(d=e[m++],f=e[m++],p=e[m++]):(d=m++,f=m++,p=m++),Bn(i,n[d*3],n[d*3+1],n[d*3+2]),Bn(a,n[f*3],n[f*3+1],n[f*3+2]),Bn(o,n[p*3],n[p*3+1],n[p*3+2]),I.sub(s,i,a),I.sub(c,a,o),I.cross(l,s,c),I.normalize(l,l);for(var h=0;h<3;h++)r[d*3+h]=l[h],r[f*3+h]=l[h],r[p*3+h]=l[h]}this.dirty()}},generateTangents:function(){if(this.vertexCount){var e=this.vertexCount,t=this.attributes;t.tangent.value||(t.tangent.value=new Float32Array(e*4));var n=t.texcoord0.value,r=t.position.value,i=t.tangent.value,a=t.normal.value;if(!n){console.warn(`Geometry without texcoords can't generate tangents.`);return}for(var o=[],s=[],c=0;c<e;c++)o[c]=[0,0,0],s[c]=[0,0,0];for(var l=[0,0,0],u=[0,0,0],d=this.indices,f=d?d.length:this.vertexCount,p,m,h,c=0;c<f;){d?(p=d[c++],m=d[c++],h=d[c++]):(p=c++,m=c++,h=c++);var g=n[p*2],_=n[m*2],v=n[h*2],y=n[p*2+1],b=n[m*2+1],x=n[h*2+1],S=r[p*3],C=r[m*3],w=r[h*3],T=r[p*3+1],E=r[m*3+1],D=r[h*3+1],O=r[p*3+2],k=r[m*3+2],A=r[h*3+2],j=C-S,M=w-S,N=E-T,ee=D-T,te=k-O,P=A-O,ne=_-g,re=v-g,ie=b-y,ae=x-y,F=1/(ne*ae-ie*re);l[0]=(ae*j-ie*M)*F,l[1]=(ae*N-ie*ee)*F,l[2]=(ae*te-ie*P)*F,u[0]=(ne*M-re*j)*F,u[1]=(ne*ee-re*N)*F,u[2]=(ne*P-re*te)*F,zn(o[p],o[p],l),zn(o[m],o[m],l),zn(o[h],o[h],l),zn(s[p],s[p],u),zn(s[m],s[m],u),zn(s[h],s[h],u)}for(var oe=Rn(),se=Rn(),ce=Rn(),c=0;c<e;c++){ce[0]=a[c*3],ce[1]=a[c*3+1],ce[2]=a[c*3+2];var le=o[c];I.scale(oe,ce,I.dot(ce,le)),I.sub(oe,le,oe),I.normalize(oe,oe),I.cross(se,ce,le),i[c*4]=oe[0],i[c*4+1]=oe[1],i[c*4+2]=oe[2],i[c*4+3]=I.dot(se,s[c])<0?-1:1}this.dirty()}},isUniqueVertex:function(){return!this.isUseIndices()||this.vertexCount===this.indices.length},generateUniqueVertex:function(){if(!(!this.vertexCount||!this.indices)){this.indices.length>65535&&(this.indices=new ct.Uint32Array(this.indices));for(var e=this.attributes,t=this.indices,n=this.getEnabledAttributes(),r={},i=0;i<n.length;i++){var a=n[i];r[a]=e[a].value,e[a].init(this.indices.length)}for(var o=0,s=0;s<t.length;s++){for(var c=t[s],i=0;i<n.length;i++)for(var a=n[i],l=e[a].value,u=e[a].size,d=0;d<u;d++)l[o*u+d]=r[a][c*u+d];t[s]=o,o++}this.dirty()}},generateBarycentric:function(){if(this.vertexCount){this.isUniqueVertex()||this.generateUniqueVertex();var e=this.attributes,t=e.barycentric.value,n=this.indices;if(!(t&&t.length===n.length*3)){t=e.barycentric.value=new Float32Array(n.length*3);for(var r=0;r<(n?n.length:this.vertexCount/3);)for(var i=0;i<3;i++){var a=n?n[r++]:r*3+i;t[a*3+i]=1}this.dirty()}}},applyTransform:function(e){var t=this.attributes,n=t.position.value,r=t.normal.value,i=t.tangent.value;e=e.array;var a=V.create();V.invert(a,e),V.transpose(a,a);var o=I.transformMat4,s=I.forEach;s(n,3,0,null,o,e),r&&s(r,3,0,null,o,a),i&&s(i,4,0,null,o,a),this.boundingBox&&this.updateBoundingBox()},dispose:function(e){var t=this._cache;t.use(e.__uid__);var n=t.get(`chunks`);if(n)for(var r=0;r<n.length;r++){for(var i=n[r],a=0;a<i.attributeBuffers.length;a++){var o=i.attributeBuffers[a];e.gl.deleteBuffer(o.buffer)}i.indicesBuffer&&e.gl.deleteBuffer(i.indicesBuffer.buffer)}if(this.__vaoCache){var s=e.getGLExtension(`OES_vertex_array_object`);for(var c in this.__vaoCache){var l=this.__vaoCache[c].vao;l&&s.deleteVertexArrayOES(l)}}this.__vaoCache={},t.deleteContext(e.__uid__)}});Y.STATIC_DRAW=Ln.STATIC_DRAW,Y.DYNAMIC_DRAW=Ln.DYNAMIC_DRAW,Y.STREAM_DRAW=Ln.STREAM_DRAW,Y.AttributeBuffer=Ln.AttributeBuffer,Y.IndicesBuffer=Ln.IndicesBuffer,Y.Attribute=Vn;var Hn=`vec3 calcAmbientSHLight(int idx, vec3 N) {
 int offset = 9 * idx;
 return ambientSHLightCoefficients[0]
 + ambientSHLightCoefficients[1] * N.x
 + ambientSHLightCoefficients[2] * N.y
 + ambientSHLightCoefficients[3] * N.z
 + ambientSHLightCoefficients[4] * N.x * N.z
 + ambientSHLightCoefficients[5] * N.z * N.y
 + ambientSHLightCoefficients[6] * N.y * N.x
 + ambientSHLightCoefficients[7] * (3.0 * N.z * N.z - 1.0)
 + ambientSHLightCoefficients[8] * (N.x * N.x - N.y * N.y);
}`,Un=`uniform vec3 `,Wn=`uniform float `,Gn=`@export clay.header.`,Kn=`@end`,qn=`:unconfigurable;`,Jn=[Gn+`directional_light`,Un+`directionalLightDirection[DIRECTIONAL_LIGHT_COUNT]`+qn,Un+`directionalLightColor[DIRECTIONAL_LIGHT_COUNT]`+qn,Kn,Gn+`ambient_light`,Un+`ambientLightColor[AMBIENT_LIGHT_COUNT]`+qn,Kn,Gn+`ambient_sh_light`,Un+`ambientSHLightColor[AMBIENT_SH_LIGHT_COUNT]`+qn,Un+`ambientSHLightCoefficients[AMBIENT_SH_LIGHT_COUNT * 9]`+qn,Hn,Kn,Gn+`ambient_cubemap_light`,Un+`ambientCubemapLightColor[AMBIENT_CUBEMAP_LIGHT_COUNT]`+qn,`uniform samplerCube ambientCubemapLightCubemap[AMBIENT_CUBEMAP_LIGHT_COUNT]`+qn,`uniform sampler2D ambientCubemapLightBRDFLookup[AMBIENT_CUBEMAP_LIGHT_COUNT]`+qn,Kn,Gn+`point_light`,Un+`pointLightPosition[POINT_LIGHT_COUNT]`+qn,Wn+`pointLightRange[POINT_LIGHT_COUNT]`+qn,Un+`pointLightColor[POINT_LIGHT_COUNT]`+qn,Kn,Gn+`spot_light`,Un+`spotLightPosition[SPOT_LIGHT_COUNT]`+qn,Un+`spotLightDirection[SPOT_LIGHT_COUNT]`+qn,Wn+`spotLightRange[SPOT_LIGHT_COUNT]`+qn,Wn+`spotLightUmbraAngleCosine[SPOT_LIGHT_COUNT]`+qn,Wn+`spotLightPenumbraAngleCosine[SPOT_LIGHT_COUNT]`+qn,Wn+`spotLightFalloffFactor[SPOT_LIGHT_COUNT]`+qn,Un+`spotLightColor[SPOT_LIGHT_COUNT]`+qn,Kn].join(`
`);K.import(Jn);var Yn=$e.extend(function(){return{color:[1,1,1],intensity:1,castShadow:!0,shadowResolution:512,group:0}},{type:``,clone:function(){var e=$e.prototype.clone.call(this);return e.color=Array.prototype.slice.call(this.color),e.intensity=this.intensity,e.castShadow=this.castShadow,e.shadowResolution=this.shadowResolution,e}}),Xn=function(e,t){this.normal=e||new L(0,1,0),this.distance=t||0};Xn.prototype={constructor:Xn,distanceToPoint:function(e){return I.dot(e.array,this.normal.array)-this.distance},projectPoint:function(e,t){t||(t=new L);var n=this.distanceToPoint(e);return I.scaleAndAdd(t.array,e.array,this.normal.array,-n),t._dirty=!0,t},normalize:function(){var e=1/I.len(this.normal.array);I.scale(this.normal.array,e),this.distance*=e},intersectFrustum:function(e){for(var t=e.vertices,n=this.normal.array,r=I.dot(t[0].array,n)>this.distance,i=1;i<8;i++)if(I.dot(t[i].array,n)>this.distance!=r)return!0},intersectLine:(function(){var e=I.create();return function(t,n,r){var i=this.distanceToPoint(t),a=this.distanceToPoint(n);if(i>0&&a>0||i<0&&a<0)return null;var o=this.normal.array,s=this.distance,c=t.array;I.sub(e,n.array,t.array),I.normalize(e,e);var l=I.dot(o,e);if(l===0)return null;r||(r=new L);var u=(I.dot(o,c)-s)/l;return I.scaleAndAdd(r.array,c,e,-u),r._dirty=!0,r}})(),applyTransform:(function(){var e=V.create(),t=R.create(),n=R.create();return n[3]=1,function(r){r=r.array,I.scale(n,this.normal.array,this.distance),R.transformMat4(n,n,r),this.distance=I.dot(n,this.normal.array),V.invert(e,r),V.transpose(e,e),t[3]=0,I.copy(t,this.normal.array),R.transformMat4(t,t,e),I.copy(this.normal.array,t)}})(),copy:function(e){I.copy(this.normal.array,e.normal.array),this.normal._dirty=!0,this.distance=e.distance},clone:function(){var e=new Xn;return e.copy(this),e}};var Zn=I.set,Qn=I.copy,$n=I.transformMat4,er=Math.min,tr=Math.max,nr=function(){this.planes=[];for(var e=0;e<6;e++)this.planes.push(new Xn);this.boundingBox=new Ze,this.vertices=[];for(var e=0;e<8;e++)this.vertices[e]=I.fromValues(0,0,0)};nr.prototype={setFromProjection:function(e){var t=this.planes,n=e.array,r=n[0],i=n[1],a=n[2],o=n[3],s=n[4],c=n[5],l=n[6],u=n[7],d=n[8],f=n[9],p=n[10],m=n[11],h=n[12],g=n[13],_=n[14],v=n[15];Zn(t[0].normal.array,o-r,u-s,m-d),t[0].distance=-(v-h),t[0].normalize(),Zn(t[1].normal.array,o+r,u+s,m+d),t[1].distance=-(v+h),t[1].normalize(),Zn(t[2].normal.array,o+i,u+c,m+f),t[2].distance=-(v+g),t[2].normalize(),Zn(t[3].normal.array,o-i,u-c,m-f),t[3].distance=-(v-g),t[3].normalize(),Zn(t[4].normal.array,o-a,u-l,m-p),t[4].distance=-(v-_),t[4].normalize(),Zn(t[5].normal.array,o+a,u+l,m+p),t[5].distance=-(v+_),t[5].normalize();var y=this.boundingBox,b=this.vertices;if(v===0){var x=c/r,S=-_/(p-1),C=-_/(p+1),w=-C/c,T=-S/c;y.min.set(-w*x,-w,C),y.max.set(w*x,w,S),Zn(b[0],-w*x,-w,C),Zn(b[1],-w*x,w,C),Zn(b[2],w*x,-w,C),Zn(b[3],w*x,w,C),Zn(b[4],-T*x,-T,S),Zn(b[5],-T*x,T,S),Zn(b[6],T*x,-T,S),Zn(b[7],T*x,T,S)}else{var E=(-1-h)/r,D=(1-h)/r,O=(1-g)/c,k=(-1-g)/c,A=(-1-_)/p,j=(1-_)/p;y.min.set(Math.min(E,D),Math.min(k,O),Math.min(j,A)),y.max.set(Math.max(D,E),Math.max(O,k),Math.max(A,j));var M=y.min.array,N=y.max.array;Zn(b[0],M[0],M[1],M[2]),Zn(b[1],M[0],N[1],M[2]),Zn(b[2],N[0],M[1],M[2]),Zn(b[3],N[0],N[1],M[2]),Zn(b[4],M[0],M[1],N[2]),Zn(b[5],M[0],N[1],N[2]),Zn(b[6],N[0],M[1],N[2]),Zn(b[7],N[0],N[1],N[2])}},getTransformedBoundingBox:(function(){var e=I.create();return function(t,n){var r=this.vertices,i=n.array,a=t.min,o=t.max,s=a.array,c=o.array,l=r[0];$n(e,l,i),Qn(s,e),Qn(c,e);for(var u=1;u<8;u++)l=r[u],$n(e,l,i),s[0]=er(e[0],s[0]),s[1]=er(e[1],s[1]),s[2]=er(e[2],s[2]),c[0]=tr(e[0],c[0]),c[1]=tr(e[1],c[1]),c[2]=tr(e[2],c[2]);return a._dirty=!0,o._dirty=!0,t}})()};var rr=1e-5,ir=function(e,t){this.origin=e||new L,this.direction=t||new L};ir.prototype={constructor:ir,intersectPlane:function(e,t){var n=e.normal.array,r=e.distance,i=this.origin.array,a=this.direction.array,o=I.dot(n,a);if(o===0)return null;t||(t=new L);var s=(I.dot(n,i)-r)/o;return I.scaleAndAdd(t.array,i,a,-s),t._dirty=!0,t},mirrorAgainstPlane:function(e){var t=I.dot(e.normal.array,this.direction.array);I.scaleAndAdd(this.direction.array,this.direction.array,e.normal.array,-t*2),this.direction._dirty=!0},distanceToPoint:(function(){var e=I.create();return function(t){I.sub(e,t,this.origin.array);var n=I.dot(e,this.direction.array);if(n<0)return I.distance(this.origin.array,t);var r=I.lenSquared(e);return Math.sqrt(r-n*n)}})(),intersectSphere:(function(){var e=I.create();return function(t,n,r){var i=this.origin.array,a=this.direction.array;t=t.array,I.sub(e,t,i);var o=I.dot(e,a),s=I.squaredLength(e)-o*o,c=n*n;if(!(s>c)){var l=Math.sqrt(c-s),u=o-l,d=o+l;return r||(r=new L),u<0?d<0?null:(I.scaleAndAdd(r.array,i,a,d),r):(I.scaleAndAdd(r.array,i,a,u),r)}}})(),intersectBoundingBox:function(e,t){var n=this.direction.array,r=this.origin.array,i=e.min.array,a=e.max.array,o=1/n[0],s=1/n[1],c=1/n[2],l,u,d,f,p,m;if(o>=0?(l=(i[0]-r[0])*o,u=(a[0]-r[0])*o):(u=(i[0]-r[0])*o,l=(a[0]-r[0])*o),s>=0?(d=(i[1]-r[1])*s,f=(a[1]-r[1])*s):(f=(i[1]-r[1])*s,d=(a[1]-r[1])*s),l>f||d>u||((d>l||l!==l)&&(l=d),(f<u||u!==u)&&(u=f),c>=0?(p=(i[2]-r[2])*c,m=(a[2]-r[2])*c):(m=(i[2]-r[2])*c,p=(a[2]-r[2])*c),l>m||p>u)||((p>l||l!==l)&&(l=p),(m<u||u!==u)&&(u=m),u<0))return null;var h=l>=0?l:u;return t||(t=new L),I.scaleAndAdd(t.array,r,n,h),t},intersectTriangle:(function(){var e=I.create(),t=I.create(),n=I.create(),r=I.create();return function(i,a,o,s,c,l){var u=this.direction.array,d=this.origin.array;i=i.array,a=a.array,o=o.array,I.sub(e,a,i),I.sub(t,o,i),I.cross(r,t,u);var f=I.dot(e,r);if(s){if(f>-rr)return null}else if(f>-rr&&f<rr)return null;I.sub(n,d,i);var p=I.dot(r,n)/f;if(p<0||p>1)return null;I.cross(r,e,n);var m=I.dot(u,r)/f;if(m<0||m>1||p+m>1)return null;I.cross(r,e,t);var h=-I.dot(n,r)/f;return h<0?null:(c||(c=new L),l&&L.set(l,1-p-m,p,m),I.scaleAndAdd(c.array,d,u,h),c)}})(),applyTransform:function(e){L.add(this.direction,this.direction,this.origin),L.transformMat4(this.origin,this.origin,e),L.transformMat4(this.direction,this.direction,e),L.sub(this.direction,this.direction,this.origin),L.normalize(this.direction,this.direction)},copy:function(e){L.copy(this.origin,e.origin),L.copy(this.direction,e.direction)},clone:function(){var e=new ir;return e.copy(this),e}};var ar=$e.extend(function(){return{projectionMatrix:new H,invProjectionMatrix:new H,viewMatrix:new H,frustum:new nr}},function(){this.update(!0)},{update:function(e){$e.prototype.update.call(this,e),H.invert(this.viewMatrix,this.worldTransform),this.updateProjectionMatrix(),H.invert(this.invProjectionMatrix,this.projectionMatrix),this.frustum.setFromProjection(this.projectionMatrix)},setViewMatrix:function(e){H.copy(this.viewMatrix,e),H.invert(this.worldTransform,e),this.decomposeWorldTransform()},decomposeProjectionMatrix:function(){},setProjectionMatrix:function(e){H.copy(this.projectionMatrix,e),H.invert(this.invProjectionMatrix,e),this.decomposeProjectionMatrix()},updateProjectionMatrix:function(){},castRay:(function(){var e=R.create();return function(t,n){var r=n===void 0?new ir:n,i=t.array[0],a=t.array[1];return R.set(e,i,a,-1,1),R.transformMat4(e,e,this.invProjectionMatrix.array),R.transformMat4(e,e,this.worldTransform.array),I.scale(r.origin.array,e,1/e[3]),R.set(e,i,a,1,1),R.transformMat4(e,e,this.invProjectionMatrix.array),R.transformMat4(e,e,this.worldTransform.array),I.scale(e,e,1/e[3]),I.sub(r.direction.array,e,r.origin.array),I.normalize(r.direction.array,r.direction.array),r.direction._dirty=!0,r.origin._dirty=!0,r}})()}),or=V.create(),sr=V.create(),cr={};function lr(e){var t=[],n=Object.keys(e);n.sort();for(var r=0;r<n.length;r++){var i=n[r];t.push(i+` `+e[i])}var a=t.join(`
`);if(cr[a])return cr[a];var o=Pe.genGUID();return cr[a]=o,o}function ur(){this.opaque=[],this.transparent=[],this._opaqueCount=0,this._transparentCount=0}ur.prototype.startCount=function(){this._opaqueCount=0,this._transparentCount=0},ur.prototype.add=function(e,t){t?this.transparent[this._transparentCount++]=e:this.opaque[this._opaqueCount++]=e},ur.prototype.endCount=function(){this.transparent.length=this._transparentCount,this.opaque.length=this._opaqueCount};var dr=$e.extend(function(){return{material:null,lights:[],viewBoundingBoxLastFrame:new Ze,shadowUniforms:{},_cameraList:[],_lightUniforms:{},_previousLightNumber:{},_lightNumber:{},_lightProgramKeys:{},_nodeRepository:{},_renderLists:new dt(20)}},function(){this._scene=this},{addToScene:function(e){e instanceof ar?(this._cameraList.length>0&&console.warn(`Found multiple camera in one scene. Use the fist one.`),this._cameraList.push(e)):e instanceof Yn&&this.lights.push(e),e.name&&(this._nodeRepository[e.name]=e)},removeFromScene:function(e){var t;e instanceof ar?(t=this._cameraList.indexOf(e),t>=0&&this._cameraList.splice(t,1)):e instanceof Yn&&(t=this.lights.indexOf(e),t>=0&&this.lights.splice(t,1)),e.name&&delete this._nodeRepository[e.name]},getNode:function(e){return this._nodeRepository[e]},setMainCamera:function(e){var t=this._cameraList.indexOf(e);t>=0&&this._cameraList.splice(t,1),this._cameraList.unshift(e)},getMainCamera:function(){return this._cameraList[0]},getLights:function(){return this.lights},updateLights:function(){var e=this.lights;this._previousLightNumber=this._lightNumber;for(var t={},n=0;n<e.length;n++){var r=e[n];if(!r.invisible){var i=r.group;t[i]||(t[i]={}),t[i][r.type]=t[i][r.type]||0,t[i][r.type]++}}for(var a in this._lightNumber=t,t)this._lightProgramKeys[a]=lr(t[a]);this._updateLightUniforms()},cloneNode:function(e){var t=e.clone(),n={};function r(e,t){n[e.__uid__]=t;for(var i=0;i<e._children.length;i++){var a=e._children[i],o=t._children[i];r(a,o)}}return r(e,t),t.traverse(function(e){e.skeleton&&(e.skeleton=e.skeleton.clone(n)),e.material&&(e.material=e.material.clone())}),t},updateRenderList:function(e,t){var n=e.__uid__,r=this._renderLists.get(n);r||(r=new ur,this._renderLists.put(n,r)),r.startCount(),t&&(this.viewBoundingBoxLastFrame.min.set(1/0,1/0,1/0),this.viewBoundingBoxLastFrame.max.set(-1/0,-1/0,-1/0));var i=this.material&&this.material.transparent||!1;return this._doUpdateRenderList(this,e,i,r,t),r.endCount(),r},getRenderList:function(e){return this._renderLists.get(e.__uid__)},_doUpdateRenderList:function(e,t,n,r,i){if(!e.invisible)for(var a=0;a<e._children.length;a++){var o=e._children[a];if(o.isRenderable()){var s=o.isSkinnedMesh()?or:o.worldTransform.array,c=o.geometry;V.multiplyAffine(sr,t.viewMatrix.array,s),(i&&!c.boundingBox||!this.isFrustumCulled(o,t,sr))&&r.add(o,o.material.transparent||n)}o._children.length>0&&this._doUpdateRenderList(o,t,n,r,i)}},isFrustumCulled:(function(){var e=new Ze,t=new H;return function(n,r,i){var a=n.boundingBox;if(a||(a=n.skeleton&&n.skeleton.boundingBox?n.skeleton.boundingBox:n.geometry.boundingBox),!a)return!1;if(t.array=i,e.transformFrom(a,t),n.castShadow&&this.viewBoundingBoxLastFrame.union(e),n.frustumCulling){if(!e.intersectBoundingBox(r.frustum.boundingBox))return!0;t.array=r.projectionMatrix.array,e.max.array[2]>0&&e.min.array[2]<0&&(e.max.array[2]=-1e-20),e.applyProjection(t);var o=e.min.array,s=e.max.array;if(s[0]<-1||o[0]>1||s[1]<-1||o[1]>1||s[2]<-1||o[2]>1)return!0}return!1}})(),_updateLightUniforms:function(){var e=this.lights;e.sort(fr);var t=this._lightUniforms;for(var n in t)for(var r in t[n])t[n][r].value.length=0;for(var i=0;i<e.length;i++){var a=e[i];if(!a.invisible){var n=a.group;for(var r in a.uniformTemplates){var o=a.uniformTemplates[r],s=o.value(a);if(s!=null){t[n]||(t[n]={}),t[n][r]||(t[n][r]={type:``,value:[]});var c=t[n][r];switch(c.type=o.type+`v`,o.type){case`1i`:case`1f`:case`t`:c.value.push(s);break;case`2f`:case`3f`:case`4f`:for(var l=0;l<s.length;l++)c.value.push(s[l]);break;default:console.error(`Unkown light uniform type `+o.type)}}}}}},getLightGroups:function(){var e=[];for(var t in this._lightNumber)e.push(t);return e},getNumberChangedLightGroups:function(){var e=[];for(var t in this._lightNumber)this.isLightNumberChanged(t)&&e.push(t);return e},isLightNumberChanged:function(e){var t=this._previousLightNumber,n=this._lightNumber;for(var r in n[e])if(!t[e]||n[e][r]!==t[e][r])return!0;for(var r in t[e])if(!n[e]||n[e][r]!==t[e][r])return!0;return!1},getLightsNumbers:function(e){return this._lightNumber[e]},getProgramKey:function(e){return this._lightProgramKeys[e]},setLightUniforms:(function(){function e(e,t,n){for(var r in e){var i=e[r];if(i.type===`tv`){if(!t.hasUniform(r))continue;for(var a=[],o=0;o<i.value.length;o++){var s=i.value[o],c=t.takeCurrentTextureSlot(n,s);a.push(c)}t.setUniform(n.gl,`1iv`,r,a)}else t.setUniform(n.gl,i.type,r,i.value)}}return function(t,n,r){e(this._lightUniforms[n],t,r),e(this.shadowUniforms,t,r)}})(),dispose:function(){this.material=null,this._opaqueList=[],this._transparentList=[],this.lights=[],this._lightUniforms={},this._lightNumber={},this._nodeRepository={}}});function fr(e,t){if(t.castShadow&&!e.castShadow)return!0}var pr=On.isPowerOfTwo,mr=[`px`,`nx`,`py`,`ny`,`pz`,`nz`],hr=q.extend(function(){return{image:{px:null,nx:null,py:null,ny:null,pz:null,nz:null},pixels:{px:null,nx:null,py:null,ny:null,pz:null,nz:null},mipmaps:[]}},{textureType:`textureCube`,update:function(e){var t=e.gl;t.bindTexture(t.TEXTURE_CUBE_MAP,this._cache.get(`webgl_texture`)),this.updateCommon(e);var n=this.format,r=this.type;t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_WRAP_S,this.getAvailableWrapS()),t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_WRAP_T,this.getAvailableWrapT()),t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_MAG_FILTER,this.getAvailableMagFilter()),t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_MIN_FILTER,this.getAvailableMinFilter());var i=e.getGLExtension(`EXT_texture_filter_anisotropic`);if(i&&this.anisotropic>1&&t.texParameterf(t.TEXTURE_CUBE_MAP,i.TEXTURE_MAX_ANISOTROPY_EXT,this.anisotropic),r===36193&&(e.getGLExtension(`OES_texture_half_float`)||(r=U.FLOAT)),this.mipmaps.length)for(var a=this.width,o=this.height,s=0;s<this.mipmaps.length;s++){var c=this.mipmaps[s];this._updateTextureData(t,c,s,a,o,n,r),a/=2,o/=2}else this._updateTextureData(t,this,0,this.width,this.height,n,r),!this.NPOT&&this.useMipmap&&t.generateMipmap(t.TEXTURE_CUBE_MAP);t.bindTexture(t.TEXTURE_CUBE_MAP,null)},_updateTextureData:function(e,t,n,r,i,a,o){for(var s=0;s<6;s++){var c=mr[s],l=t.image&&t.image[c];l?e.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+s,n,a,a,o,l):e.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+s,n,a,r,i,0,a,o,t.pixels&&t.pixels[c])}},generateMipmap:function(e){var t=e.gl;this.useMipmap&&!this.NPOT&&(t.bindTexture(t.TEXTURE_CUBE_MAP,this._cache.get(`webgl_texture`)),t.generateMipmap(t.TEXTURE_CUBE_MAP))},bind:function(e){e.gl.bindTexture(e.gl.TEXTURE_CUBE_MAP,this.getWebGLTexture(e))},unbind:function(e){e.gl.bindTexture(e.gl.TEXTURE_CUBE_MAP,null)},isPowerOfTwo:function(){return this.image.px?pr(this.image.px.width)&&pr(this.image.px.height):pr(this.width)&&pr(this.height)},isRenderable:function(){return this.image.px?gr(this.image.px)&&gr(this.image.nx)&&gr(this.image.py)&&gr(this.image.ny)&&gr(this.image.pz)&&gr(this.image.nz):!!(this.width&&this.height)},load:function(e,t){var n=0,r=this;return Pe.each(e,function(e,i){var a=ct.createImage();t&&(a.crossOrigin=t),a.onload=function(){n--,n===0&&(r.dirty(),r.trigger(`success`,r))},a.onerror=function(){n--},n++,a.src=e,r.image[i]=a}),this}});Object.defineProperty(hr.prototype,"width",{get:function(){return this.image&&this.image.px?this.image.px.width:this._width},set:function(e){this.image&&this.image.px?console.warn(`Texture from image can't set width`):(this._width!==e&&this.dirty(),this._width=e)}}),Object.defineProperty(hr.prototype,"height",{get:function(){return this.image&&this.image.px?this.image.px.height:this._height},set:function(e){this.image&&this.image.px?console.warn(`Texture from image can't set height`):(this._height!==e&&this.dirty(),this._height=e)}});function gr(e){return e.width>0&&e.height>0}var _r=ar.extend({fov:50,aspect:1,near:.1,far:2e3},{updateProjectionMatrix:function(){var e=this.fov/180*Math.PI;this.projectionMatrix.perspective(e,this.aspect,this.near,this.far)},decomposeProjectionMatrix:function(){var e=this.projectionMatrix.array,t=Math.atan(1/e[5])*2;this.fov=t/Math.PI*180,this.aspect=e[5]/e[0],this.near=e[14]/(e[10]-1),this.far=e[14]/(e[10]+1)},clone:function(){var e=ar.prototype.clone.call(this);return e.fov=this.fov,e.aspect=this.aspect,e.near=this.near,e.far=this.far,e}}),vr=`framebuffer`,yr=`renderbuffer`,br=yr+`_width`,xr=yr+`_height`,Sr=yr+`_attached`,Cr=`depthtexture_attached`,wr=U.FRAMEBUFFER,Tr=U.RENDERBUFFER,Er=U.DEPTH_ATTACHMENT,Dr=U.COLOR_ATTACHMENT0,Or=Fe.extend({depthBuffer:!0,viewport:null,_width:0,_height:0,_textures:null,_boundRenderer:null},function(){this._cache=new Dn,this._textures={}},{getTextureWidth:function(){return this._width},getTextureHeight:function(){return this._height},bind:function(e){if(e.__currentFrameBuffer){if(e.__currentFrameBuffer===this)return;console.warn(`Renderer already bound with another framebuffer. Unbind it first`)}e.__currentFrameBuffer=this;var t=e.gl;t.bindFramebuffer(wr,this._getFrameBufferGL(e)),this._boundRenderer=e;var n=this._cache;n.put(`viewport`,e.viewport);var r=!1,i,a;for(var o in this._textures){r=!0;var s=this._textures[o];s&&(i=s.texture.width,a=s.texture.height,this._doAttach(e,s.texture,o,s.target))}this._width=i,this._height=a,!r&&this.depthBuffer&&console.error(`Must attach texture before bind, or renderbuffer may have incorrect width and height.`),this.viewport?e.setViewport(this.viewport):e.setViewport(0,0,i,a,1);var c=n.get(`attached_textures`);if(c){for(var o in c)if(!this._textures[o]){var l=c[o];this._doDetach(t,o,l)}}if(!n.get(Cr)&&this.depthBuffer){n.miss(yr)&&n.put(yr,t.createRenderbuffer());var u=n.get(yr);(i!==n.get(br)||a!==n.get(xr))&&(t.bindRenderbuffer(Tr,u),t.renderbufferStorage(Tr,t.DEPTH_COMPONENT16,i,a),n.put(br,i),n.put(xr,a),t.bindRenderbuffer(Tr,null)),n.get(Sr)||(t.framebufferRenderbuffer(wr,Er,Tr,u),n.put(Sr,!0))}},unbind:function(e){e.__currentFrameBuffer=null,e.gl.bindFramebuffer(wr,null),this._boundRenderer=null,this._cache.use(e.__uid__);var t=this._cache.get(`viewport`);t&&e.setViewport(t),this.updateMipmap(e)},updateMipmap:function(e){var t=e.gl;for(var n in this._textures){var r=this._textures[n];if(r){var i=r.texture;if(!i.NPOT&&i.useMipmap&&i.minFilter===q.LINEAR_MIPMAP_LINEAR){var a=i.textureType===`textureCube`?U.TEXTURE_CUBE_MAP:U.TEXTURE_2D;t.bindTexture(a,i.getWebGLTexture(e)),t.generateMipmap(a),t.bindTexture(a,null)}}}},checkStatus:function(e){return e.checkFramebufferStatus(wr)},_getFrameBufferGL:function(e){var t=this._cache;return t.use(e.__uid__),t.miss(vr)&&t.put(vr,e.gl.createFramebuffer()),t.get(vr)},attach:function(e,t,n){if(!e.width)throw Error(`The texture attached to color buffer is not a valid.`);t=t||Dr,n=n||U.TEXTURE_2D;var r=this._boundRenderer,i=r&&r.gl,a;if(i){var o=this._cache;o.use(r.__uid__),a=o.get(`attached_textures`)}var s=this._textures[t];if(!(s&&s.target===n&&s.texture===e&&a&&a[t]!=null)){var c=!0;r&&(c=this._doAttach(r,e,t,n),this.viewport||r.setViewport(0,0,e.width,e.height,1)),c&&(this._textures[t]=this._textures[t]||{},this._textures[t].texture=e,this._textures[t].target=n)}},_doAttach:function(e,t,n,r){var i=e.gl,a=t.getWebGLTexture(e),o=this._cache.get(`attached_textures`);if(o&&o[n]){var s=o[n];if(s.texture===t&&s.target===r)return}n=+n;var c=!0;if((n===Er||n===U.DEPTH_STENCIL_ATTACHMENT)&&(e.getGLExtension(`WEBGL_depth_texture`)||(console.error(`Depth texture is not supported by the browser`),c=!1),t.format!==U.DEPTH_COMPONENT&&t.format!==U.DEPTH_STENCIL&&(console.error(`The texture attached to depth buffer is not a valid.`),c=!1),c)){var l=this._cache.get(yr);l&&(i.framebufferRenderbuffer(wr,Er,Tr,null),i.deleteRenderbuffer(l),this._cache.put(yr,!1)),this._cache.put(Sr,!1),this._cache.put(Cr,!0)}return i.framebufferTexture2D(wr,n,r,a,0),o||(o={},this._cache.put(`attached_textures`,o)),o[n]=o[n]||{},o[n].texture=t,o[n].target=r,c},_doDetach:function(e,t,n){e.framebufferTexture2D(wr,t,n,null,0);var r=this._cache.get(`attached_textures`);r&&r[t]&&(r[t]=null),(t===Er||t===U.DEPTH_STENCIL_ATTACHMENT)&&this._cache.put(Cr,!1)},detach:function(e,t){this._textures[e]=null,this._boundRenderer&&(this._cache.use(this._boundRenderer.__uid__),this._doDetach(this._boundRenderer.gl,e,t))},dispose:function(e){var t=e.gl,n=this._cache;n.use(e.__uid__);var r=n.get(yr);r&&t.deleteRenderbuffer(r);var i=n.get(vr);i&&t.deleteFramebuffer(i),n.deleteContext(e.__uid__),this._textures={}}});Or.DEPTH_ATTACHMENT=Er,Or.COLOR_ATTACHMENT0=Dr,Or.STENCIL_ATTACHMENT=U.STENCIL_ATTACHMENT,Or.DEPTH_STENCIL_ATTACHMENT=U.DEPTH_STENCIL_ATTACHMENT;var kr=[`px`,`nx`,`py`,`ny`,`pz`,`nz`],Ar=Fe.extend(function(){var e={position:new L,far:1e3,near:.1,texture:null,shadowMapPass:null},t=e._cameras={px:new _r({fov:90}),nx:new _r({fov:90}),py:new _r({fov:90}),ny:new _r({fov:90}),pz:new _r({fov:90}),nz:new _r({fov:90})};return t.px.lookAt(L.POSITIVE_X,L.NEGATIVE_Y),t.nx.lookAt(L.NEGATIVE_X,L.NEGATIVE_Y),t.py.lookAt(L.POSITIVE_Y,L.POSITIVE_Z),t.ny.lookAt(L.NEGATIVE_Y,L.NEGATIVE_Z),t.pz.lookAt(L.POSITIVE_Z,L.NEGATIVE_Y),t.nz.lookAt(L.NEGATIVE_Z,L.NEGATIVE_Y),e._frameBuffer=new Or,e},{getCamera:function(e){return this._cameras[e]},render:function(e,t,n){var r=e.gl;n||t.update();for(var i=this.texture.width,a=2*Math.atan(i/(i-.5))/Math.PI*180,o=0;o<6;o++){var s=kr[o],c=this._cameras[s];if(L.copy(c.position,this.position),c.far=this.far,c.near=this.near,c.fov=a,this.shadowMapPass){c.update();var l=t.getBoundingBox();l.applyTransform(c.viewMatrix),t.viewBoundingBoxLastFrame.copy(l),this.shadowMapPass.render(e,t,c,!0)}this._frameBuffer.attach(this.texture,r.COLOR_ATTACHMENT0,r.TEXTURE_CUBE_MAP_POSITIVE_X+o),this._frameBuffer.bind(e),e.render(t,c,!0),this._frameBuffer.unbind(e)}},dispose:function(e){this._frameBuffer.dispose(e)}}),jr=Y.extend({dynamic:!1,widthSegments:1,heightSegments:1},function(){this.build()},{build:function(){for(var e=this.heightSegments,t=this.widthSegments,n=this.attributes,r=[],i=[],a=[],o=[],s=0;s<=e;s++)for(var c=s/e,l=0;l<=t;l++){var u=l/t;if(r.push([2*u-1,2*c-1,0]),i&&i.push([u,c]),a&&a.push([0,0,1]),l<t&&s<e){var d=l+s*(t+1);o.push([d,d+1,d+t+1]),o.push([d+t+1,d+1,d+t+2])}}n.position.fromArray(r),n.texcoord0.fromArray(i),n.normal.fromArray(a),this.initIndicesFromArray(o),this.boundingBox=new Ze,this.boundingBox.min.set(-1,-1,0),this.boundingBox.max.set(1,1,0)}}),Mr=new H,Nr=Y.extend({dynamic:!1,widthSegments:1,heightSegments:1,depthSegments:1,inside:!1},function(){this.build()},{build:function(){var e={px:Pr(`px`,this.depthSegments,this.heightSegments),nx:Pr(`nx`,this.depthSegments,this.heightSegments),py:Pr(`py`,this.widthSegments,this.depthSegments),ny:Pr(`ny`,this.widthSegments,this.depthSegments),pz:Pr(`pz`,this.widthSegments,this.heightSegments),nz:Pr(`nz`,this.widthSegments,this.heightSegments)},t=[`position`,`texcoord0`,`normal`],n=0,r=0;for(var i in e)n+=e[i].vertexCount,r+=e[i].indices.length;for(var a=0;a<t.length;a++)this.attributes[t[a]].init(n);this.indices=new ct.Uint16Array(r);var o=0,s=0;for(var i in e){for(var c=e[i],a=0;a<t.length;a++)for(var l=t[a],u=c.attributes[l].value,d=c.attributes[l].size,f=l===`normal`,p=0;p<u.length;p++){var m=u[p];this.inside&&f&&(m=-m),this.attributes[l].value[p+d*s]=m}for(var h=c.indices.length,p=0;p<c.indices.length;p++)this.indices[p+o]=s+c.indices[this.inside?h-p-1:p];o+=c.indices.length,s+=c.vertexCount}this.boundingBox=new Ze,this.boundingBox.max.set(1,1,1),this.boundingBox.min.set(-1,-1,-1)}});function Pr(e,t,n){Mr.identity();var r=new jr({widthSegments:t,heightSegments:n});switch(e){case`px`:H.translate(Mr,Mr,L.POSITIVE_X),H.rotateY(Mr,Mr,Math.PI/2);break;case`nx`:H.translate(Mr,Mr,L.NEGATIVE_X),H.rotateY(Mr,Mr,-Math.PI/2);break;case`py`:H.translate(Mr,Mr,L.POSITIVE_Y),H.rotateX(Mr,Mr,-Math.PI/2);break;case`ny`:H.translate(Mr,Mr,L.NEGATIVE_Y),H.rotateX(Mr,Mr,Math.PI/2);break;case`pz`:H.translate(Mr,Mr,L.POSITIVE_Z);break;case`nz`:H.translate(Mr,Mr,L.NEGATIVE_Z),H.rotateY(Mr,Mr,Math.PI);break}return r.applyTransform(Mr),r}K.import(`@export clay.skybox.vertex
#define SHADER_NAME skybox
uniform mat4 world : WORLD;
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
attribute vec3 position : POSITION;
varying vec3 v_WorldPosition;
void main()
{
 v_WorldPosition = (world * vec4(position, 1.0)).xyz;
 gl_Position = worldViewProjection * vec4(position, 1.0);
}
@end
@export clay.skybox.fragment
#define PI 3.1415926
uniform mat4 viewInverse : VIEWINVERSE;
#ifdef EQUIRECTANGULAR
uniform sampler2D environmentMap;
#else
uniform samplerCube environmentMap;
#endif
uniform float lod: 0.0;
varying vec3 v_WorldPosition;
@import clay.util.rgbm
@import clay.util.srgb
@import clay.util.ACES
void main()
{
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(v_WorldPosition - eyePos);
#ifdef EQUIRECTANGULAR
 float phi = acos(V.y);
 float theta = atan(-V.x, V.z) + PI * 0.5;
 vec2 uv = vec2(theta / 2.0 / PI, phi / PI);
 vec4 texel = decodeHDR(texture2D(environmentMap, fract(uv)));
#else
 #if defined(LOD) || defined(SUPPORT_TEXTURE_LOD)
 vec4 texel = decodeHDR(textureCubeLodEXT(environmentMap, V, lod));
 #else
 vec4 texel = decodeHDR(textureCube(environmentMap, V));
 #endif
#endif
#ifdef SRGB_DECODE
 texel = sRGBToLinear(texel);
#endif
#ifdef TONEMAPPING
 texel.rgb = ACESToneMapping(texel.rgb);
#endif
#ifdef SRGB_ENCODE
 texel = linearTosRGB(texel);
#endif
 gl_FragColor = encodeHDR(vec4(texel.rgb, 1.0));
}
@end`);var Fr=tt.extend(function(){var e=new Mt({shader:new K({vertex:K.source(`clay.skybox.vertex`),fragment:K.source(`clay.skybox.fragment`)}),depthMask:!1});return{scene:null,geometry:new Nr,material:e,environmentMap:null,culling:!1,_dummyCamera:new _r}},function(){var e=this.scene;e&&this.attachScene(e),this.environmentMap&&this.setEnvironmentMap(this.environmentMap)},{attachScene:function(e){this.scene&&this.detachScene(),e.skybox=this,this.scene=e,e.on(`beforerender`,this._beforeRenderScene,this)},detachScene:function(){this.scene&&(this.scene.off(`beforerender`,this._beforeRenderScene),this.scene.skybox=null),this.scene=null},dispose:function(e){this.detachScene(),this.geometry.dispose(e)},setEnvironmentMap:function(e){e.textureType===`texture2D`?(this.material.define(`EQUIRECTANGULAR`),e.minFilter=q.LINEAR):this.material.undefine(`EQUIRECTANGULAR`),this.material.set(`environmentMap`,e)},getEnvironmentMap:function(){return this.material.get(`environmentMap`)},_beforeRenderScene:function(e,t,n){this.renderSkybox(e,n)},renderSkybox:function(e,t){var n=this._dummyCamera;n.aspect=e.getViewportAspect(),n.fov=t.fov||50,n.updateProjectionMatrix(),H.invert(n.invProjectionMatrix,n.projectionMatrix),n.worldTransform.copy(t.worldTransform),n.viewMatrix.copy(t.viewMatrix),this.position.copy(t.getWorldPosition()),this.update(),e.gl.disable(e.gl.BLEND),this.material.get(`lod`)>0?this.material.define(`fragment`,`LOD`):this.material.undefine(`fragment`,`LOD`),e.renderPass([this],n)}}),Ir=Fr,Lr=542327876,Rr=131072,zr=512,Br=4;function Vr(e){return e.charCodeAt(0)+(e.charCodeAt(1)<<8)+(e.charCodeAt(2)<<16)+(e.charCodeAt(3)<<24)}var Hr=31,Ur=Vr(`DXT1`),Wr=Vr(`DXT3`),Gr=Vr(`DXT5`),Kr=0,qr=1,Jr=2,Yr=3,Xr=4,Zr=7,Qr=20,$r=21,ei=28,ti={parse:function(e,t){var n=new Int32Array(e,0,Hr);if(n[Kr]!==Lr||!n(Qr)&Br)return null;var r=n($r),i=n[Xr],a=n[Yr],o=n[ei]&zr,s=n[Jr]&Rr,c,l;switch(r){case Ur:c=8,l=q.COMPRESSED_RGB_S3TC_DXT1_EXT;break;case Wr:c=16,l=q.COMPRESSED_RGBA_S3TC_DXT3_EXT;break;case Gr:c=16,l=q.COMPRESSED_RGBA_S3TC_DXT5_EXT;break;default:return null}var u=n[qr]+4,d=o?6:1,f=1;s&&(f=Math.max(1,n[Zr]));for(var p=[],m=0;m<d;m++){var h=i,g=a;p[m]=new J({width:h,height:g,format:l});for(var _=[],v=0;v<f;v++){var y=Math.max(4,h)/4*Math.max(4,g)/4*c,b=new Uint8Array(e,u,y);u+=y,h*=.5,g*=.5,_[v]=b}p[m].pixels=_[0],s&&(p[m].mipmaps=_)}if(t)t.width=p[0].width,t.height=p[0].height,t.format=p[0].format,t.pixels=p[0].pixels,t.mipmaps=p[0].mipmaps;else return p[0]}},ni=String.fromCharCode,ri=8,ii=32767;function ai(e,t,n,r){if(e[3]>0){var i=2**(e[3]-128-8+r);t[n+0]=e[0]*i,t[n+1]=e[1]*i,t[n+2]=e[2]*i}else t[n+0]=0,t[n+1]=0,t[n+2]=0;return t[n+3]=1,t}function oi(e,t,n){for(var r=``,i=t;i<n;i++)r+=ni(e[i]);return r}function si(e,t){t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3]}function ci(e,t,n,r){for(var i=0,a=0,o=r;o>0;)if(e[a][0]=t[n++],e[a][1]=t[n++],e[a][2]=t[n++],e[a][3]=t[n++],e[a][0]===1&&e[a][1]===1&&e[a][2]===1){for(var s=e[a][3]<<i>>>0;s>0;s--)si(e[a-1],e[a]),a++,o--;i+=8}else a++,o--,i=0;return n}function li(e,t,n,r){if(r<ri|r>ii)return ci(e,t,n,r);var i=t[n++];if(i!=2)return ci(e,t,n-1,r);if(e[0][1]=t[n++],e[0][2]=t[n++],i=t[n++],(e[0][2]<<8>>>0|i)>>>0!==r)return null;for(var i=0;i<4;i++)for(var a=0;a<r;){var o=t[n++];if(o>128){o=(o&127)>>>0;for(var s=t[n++];o--;)e[a++][i]=s}else for(;o--;)e[a++][i]=t[n++]}return n}var ui={parseRGBE:function(e,t,n){n==null&&(n=0);var r=new Uint8Array(e),i=r.length;if(oi(r,0,2)===`#?`){for(var a=2;a<i&&!(ni(r[a])===`
`&&ni(r[a+1])===`
`);a++);if(!(a>=i)){a+=2;for(var o=``;a<i;a++){var s=ni(r[a]);if(s===`
`)break;o+=s}var c=o.split(` `),l=parseInt(c[1]),u=parseInt(c[3]);if(!(!u||!l)){for(var d=a+1,f=[],p=0;p<u;p++){f[p]=[];for(var m=0;m<4;m++)f[p][m]=0}for(var h=new Float32Array(u*l*4),g=0,_=0;_<l;_++){var d=li(f,r,d,u);if(!d)return null;for(var p=0;p<u;p++)ai(f[p],h,g,n),g+=4}return t||(t=new J),t.width=u,t.height=l,t.pixels=h,t.type=q.FLOAT,t}}}},parseRGBEFromPNG:function(e){}},di={loadTexture:function(e,t,n,r){var i;if(typeof t==`function`?(n=t,r=n,t={}):t=t||{},typeof e==`string`){if(e.match(/.hdr$/)||t.fileType===`hdr`)return i=new J({width:0,height:0,sRGB:!1}),di._fetchTexture(e,function(e){ui.parseRGBE(e,i,t.exposure),i.dirty(),n&&n(i)},r),i;e.match(/.dds$/)||t.fileType===`dds`?(i=new J({width:0,height:0}),di._fetchTexture(e,function(e){ti.parse(e,i),i.dirty(),n&&n(i)},r)):(i=new J,i.load(e),i.success(n),i.error(r))}else typeof e==`object`&&e.px!==void 0&&(i=new hr,i.load(e),i.success(n),i.error(r));return i},loadPanorama:function(e,t,n,r,i,a){var o=this;typeof r==`function`?(i=r,a=i,r={}):r=r||{},di.loadTexture(t,r,function(t){t.flipY=r.flipY||!1,o.panoramaToCubeMap(e,t,n,r),t.dispose(e),i&&i(n)},a)},panoramaToCubeMap:function(e,t,n,r){var i=new Ar,a=new Ir({scene:new dr});return a.setEnvironmentMap(t),r=r||{},r.encodeRGBM&&a.material.define(`fragment`,`RGBM_ENCODE`),n.sRGB=t.sRGB,i.texture=n,i.render(e,a.scene),i.texture=null,i.dispose(e),n},heightToNormal:function(e,t){var n=document.createElement(`canvas`),r=n.width=e.width,i=n.height=e.height,a=n.getContext(`2d`);a.drawImage(e,0,0,r,i),t=t||!1;for(var o=a.getImageData(0,0,r,i),s=a.createImageData(r,i),c=0;c<o.data.length;c+=4){if(t){var l=o.data[c],u=o.data[c+1],d=o.data[c+2];if(Math.abs(l-u)+Math.abs(u-d)>20)return console.warn(`Given image is not a height map`),e}var f,p,m,h;c%(r*4)==0?(f=o.data[c],m=o.data[c+4]):c%(r*4)==(r-1)*4?(f=o.data[c-4],m=o.data[c]):(f=o.data[c-4],m=o.data[c+4]),c<r*4?(p=o.data[c],h=o.data[c+r*4]):c>r*(i-1)*4?(p=o.data[c-r*4],h=o.data[c]):(p=o.data[c-r*4],h=o.data[c+r*4]),s.data[c]=f-m+127,s.data[c+1]=p-h+127,s.data[c+2]=255,s.data[c+3]=255}return a.putImageData(s,0,0),n},isHeightImage:function(e,t,n){if(!e||!e.width||!e.height)return!1;var r=document.createElement(`canvas`),i=r.getContext(`2d`),a=t||32;n=n||20,r.width=r.height=a,i.drawImage(e,0,0,a,a);for(var o=i.getImageData(0,0,a,a),s=0;s<o.data.length;s+=4){var c=o.data[s],l=o.data[s+1],u=o.data[s+2];if(Math.abs(c-l)+Math.abs(l-u)>n)return!1}return!0},_fetchTexture:function(e,t,n){ct.request.get({url:e,responseType:`arraybuffer`,onload:t,onerror:n})},createChessboard:function(e,t,n,r){e=e||512,t=t||64,n=n||`black`,r=r||`white`;var i=Math.ceil(e/t),a=document.createElement(`canvas`);a.width=e,a.height=e;var o=a.getContext(`2d`);o.fillStyle=r,o.fillRect(0,0,e,e),o.fillStyle=n;for(var s=0;s<i;s++)for(var c=0;c<i;c++)(c%2?s%2:s%2-1)&&o.fillRect(s*t,c*t,t,t);return new J({image:a,anisotropic:8})},createBlank:function(e){var t=document.createElement(`canvas`);t.width=1,t.height=1;var n=t.getContext(`2d`);return n.fillStyle=e,n.fillRect(0,0,1,1),new J({image:t})}};function fi(e){return e&&typeof e==`object`&&!Array.isArray(e)&&typeof e.count==`function`&&typeof e.getItem==`function`&&typeof e.getSource!=`function`&&(e.getSource=function(){return{sourceFormat:`original`,seriesLayoutBy:`column`,startIndex:0,dimensionsDefine:null}},e.persistent==null&&(e.persistent=!0)),e}function pi(e,t){if(!e.__ECGLOnRefresh){e.__ECGLOnRefresh=!0;var n=e._refresh?`_refresh`:`refreshImmediately`,r=e[n];e[n]=function(){r.apply(this,arguments),t()}}}var mi=[`mousedown`,`mouseup`,`mousemove`,`mouseover`,`mouseout`,`click`,`dblclick`,`contextmenu`];function hi(e){return`_on`+e}var gi=function(e){var t=this;this._texture=new J({anisotropic:32,flipY:!1,surface:this,dispose:function(e){t.dispose(),J.prototype.dispose.call(this,e)}}),mi.forEach(function(e){this[hi(e)]=function(t){t.triangle&&this._meshes.forEach(function(n){this.dispatchEvent(e,n,t.triangle,t.point)},this)}},this),this._meshes=[],e&&this.setECharts(e),this.onupdate=null};gi.prototype={constructor:gi,getTexture:function(){return this._texture},setECharts:function(e){this._chart=e;var t=e.getDom();if(!(t instanceof HTMLCanvasElement))console.error(`ECharts must init on canvas if it is used as texture.`),t=document.createElement(`canvas`);else{var n=this;pi(e.getZr(),function(){n._texture.dirty(),n.onupdate&&n.onupdate()})}this._texture.image=t,this._texture.dirty(),this.onupdate&&this.onupdate()},dispatchEvent:function(){var e=new L,t=new L,n=new L,r=new G,i=new G,a=new G,o=new G,s=new L;return function(c,l,u,d){var f=l.geometry,p=f.attributes.position,m=f.attributes.texcoord0,h=L.dot,g=L.cross;p.get(u[0],e.array),p.get(u[1],t.array),p.get(u[2],n.array),m.get(u[0],r.array),m.get(u[1],i.array),m.get(u[2],a.array),g(s,t,n);var _=h(e,s),v=h(d,s)/_;g(s,n,e);var y=h(d,s)/_;g(s,e,t);var b=h(d,s)/_;G.scale(o,r,v),G.scaleAndAdd(o,o,i,y),G.scaleAndAdd(o,o,a,b);var x=o.x*this._chart.getWidth(),S=o.y*this._chart.getHeight();this._chart.getZr().handler.dispatch(c,{zrX:x,zrY:S})}}(),attachToMesh:function(e){this._meshes.indexOf(e)>=0||(mi.forEach(function(t){e.on(t,this[hi(t)],this)},this),this._meshes.push(e))},detachFromMesh:function(e){var t=this._meshes.indexOf(e);t>=0&&this._meshes.splice(t,1),mi.forEach(function(t){e.off(t,this[hi(t)])},this)},dispose:function(){this._meshes.forEach(function(e){this.detachFromMesh(e)},this)}};var _i=ar.extend({left:-1,right:1,near:-1,far:1,top:1,bottom:-1},{updateProjectionMatrix:function(){this.projectionMatrix.ortho(this.left,this.right,this.bottom,this.top,this.near,this.far)},decomposeProjectionMatrix:function(){var e=this.projectionMatrix.array;this.left=(-1-e[12])/e[0],this.right=(1-e[12])/e[0],this.top=(1-e[13])/e[5],this.bottom=(-1-e[13])/e[5],this.near=-(-1-e[14])/e[10],this.far=-(1-e[14])/e[10]},clone:function(){var e=ar.prototype.clone.call(this);return e.left=this.left,e.right=this.right,e.near=this.near,e.far=this.far,e.top=this.top,e.bottom=this.bottom,e}});K.import(`
@export clay.compositor.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;
varying vec2 v_Texcoord;
void main()
{
 v_Texcoord = texcoord;
 gl_Position = worldViewProjection * vec4(position, 1.0);
}
@end`);var vi=new tt({geometry:new jr,frustumCulling:!1}),yi=new _i,bi=Fe.extend(function(){return{fragment:``,outputs:null,material:null,blendWithPrevious:!1,clearColor:!1,clearDepth:!0}},function(){var e=new Mt({shader:new K(K.source(`clay.compositor.vertex`),this.fragment)});e.enableTexturesAll(),this.material=e},{setUniform:function(e,t){this.material.setUniform(e,t)},getUniform:function(e){var t=this.material.uniforms[e];if(t)return t.value},attachOutput:function(e,t){this.outputs||(this.outputs={}),t=t||U.COLOR_ATTACHMENT0,this.outputs[t]=e},detachOutput:function(e){for(var t in this.outputs)this.outputs[t]===e&&(this.outputs[t]=null)},bind:function(e,t){if(this.outputs)for(var n in this.outputs){var r=this.outputs[n];r&&t.attach(r,n)}t&&t.bind(e)},unbind:function(e,t){t.unbind(e)},render:function(e,t){var n=e.gl;if(t){this.bind(e,t);var r=e.getGLExtension(`EXT_draw_buffers`);if(r&&this.outputs){var i=[];for(var a in this.outputs)a=+a,a>=n.COLOR_ATTACHMENT0&&a<=n.COLOR_ATTACHMENT0+8&&i.push(a);r.drawBuffersEXT(i)}}this.trigger(`beforerender`,this,e);var o=this.clearDepth?n.DEPTH_BUFFER_BIT:0;if(n.depthMask(!0),this.clearColor){o|=n.COLOR_BUFFER_BIT,n.colorMask(!0,!0,!0,!0);var s=this.clearColor;Array.isArray(s)&&n.clearColor(s[0],s[1],s[2],s[3])}n.clear(o),this.blendWithPrevious?(n.enable(n.BLEND),this.material.transparent=!0):(n.disable(n.BLEND),this.material.transparent=!1),this.renderQuad(e),this.trigger(`afterrender`,this,e),t&&this.unbind(e,t)},renderQuad:function(e){vi.material=this.material,e.renderPass([vi],yi)},dispose:function(e){}}),xi=`#define SAMPLE_NUMBER 1024
#define PI 3.14159265358979
uniform sampler2D normalDistribution;
uniform vec2 viewportSize : [512, 256];
const vec3 N = vec3(0.0, 0.0, 1.0);
const float fSampleNumber = float(SAMPLE_NUMBER);
vec3 importanceSampleNormal(float i, float roughness, vec3 N) {
 vec3 H = texture2D(normalDistribution, vec2(roughness, i)).rgb;
 vec3 upVector = abs(N.y) > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
 vec3 tangentX = normalize(cross(N, upVector));
 vec3 tangentZ = cross(N, tangentX);
 return normalize(tangentX * H.x + N * H.y + tangentZ * H.z);
}
float G_Smith(float roughness, float NoV, float NoL) {
 float k = roughness * roughness / 2.0;
 float G1V = NoV / (NoV * (1.0 - k) + k);
 float G1L = NoL / (NoL * (1.0 - k) + k);
 return G1L * G1V;
}
void main() {
 vec2 uv = gl_FragCoord.xy / viewportSize;
 float NoV = uv.x;
 float roughness = uv.y;
 vec3 V;
 V.x = sqrt(1.0 - NoV * NoV);
 V.y = 0.0;
 V.z = NoV;
 float A = 0.0;
 float B = 0.0;
 for (int i = 0; i < SAMPLE_NUMBER; i++) {
 vec3 H = importanceSampleNormal(float(i) / fSampleNumber, roughness, N);
 vec3 L = reflect(-V, H);
 float NoL = clamp(L.z, 0.0, 1.0);
 float NoH = clamp(H.z, 0.0, 1.0);
 float VoH = clamp(dot(V, H), 0.0, 1.0);
 if (NoL > 0.0) {
 float G = G_Smith(roughness, NoV, NoL);
 float G_Vis = G * VoH / (NoH * NoV);
 float Fc = pow(1.0 - VoH, 5.0);
 A += (1.0 - Fc) * G_Vis;
 B += Fc * G_Vis;
 }
 }
 gl_FragColor = vec4(vec2(A, B) / fSampleNumber, 0.0, 1.0);
}
`,Si=`#define SHADER_NAME prefilter
#define SAMPLE_NUMBER 1024
#define PI 3.14159265358979
uniform mat4 viewInverse : VIEWINVERSE;
uniform samplerCube environmentMap;
uniform sampler2D normalDistribution;
uniform float roughness : 0.5;
varying vec2 v_Texcoord;
varying vec3 v_WorldPosition;
@import clay.util.rgbm
vec3 importanceSampleNormal(float i, float roughness, vec3 N) {
 vec3 H = texture2D(normalDistribution, vec2(roughness, i)).rgb;
 vec3 upVector = abs(N.y) > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
 vec3 tangentX = normalize(cross(N, upVector));
 vec3 tangentZ = cross(N, tangentX);
 return normalize(tangentX * H.x + N * H.y + tangentZ * H.z);
}
void main() {
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(v_WorldPosition - eyePos);
 vec3 N = V;
 vec3 prefilteredColor = vec3(0.0);
 float totalWeight = 0.0;
 float fMaxSampleNumber = float(SAMPLE_NUMBER);
 for (int i = 0; i < SAMPLE_NUMBER; i++) {
 vec3 H = importanceSampleNormal(float(i) / fMaxSampleNumber, roughness, N);
 vec3 L = reflect(-V, H);
 float NoL = clamp(dot(N, L), 0.0, 1.0);
 if (NoL > 0.0) {
 prefilteredColor += decodeHDR(textureCube(environmentMap, L)).rgb * NoL;
 totalWeight += NoL;
 }
 }
 gl_FragColor = encodeHDR(vec4(prefilteredColor / totalWeight, 1.0));
}
`,Ci={},wi=[`px`,`nx`,`py`,`ny`,`pz`,`nz`];Ci.prefilterEnvironmentMap=function(e,t,n,r,i){(!i||!r)&&(r=Ci.generateNormalDistribution(),i=Ci.integrateBRDF(e,r)),n=n||{};var a=n.width||64,o=n.height||64,s=n.type||t.type,c=new hr({width:a,height:o,type:s,flipY:!1,mipmaps:[]});c.isPowerOfTwo()||console.warn(`Width and height must be power of two to enable mipmap.`);var l=Math.log(Math.min(a,o))/Math.log(2)+1,u=new Mt({shader:new K({vertex:K.source(`clay.skybox.vertex`),fragment:Si})});u.set(`normalDistribution`,r),n.encodeRGBM&&u.define(`fragment`,`RGBM_ENCODE`),n.decodeRGBM&&u.define(`fragment`,`RGBM_DECODE`);var d=new dr,f;if(t.textureType===`texture2D`){var p=new hr({width:a,height:o,type:s===q.FLOAT?q.HALF_FLOAT:s});di.panoramaToCubeMap(e,t,p,{encodeRGBM:n.decodeRGBM}),t=p}f=new Fr({scene:d,material:u}),f.material.set(`environmentMap`,t);var m=new Ar({texture:c});n.encodeRGBM&&(s=c.type=q.UNSIGNED_BYTE);for(var h=new J({width:a,height:o,type:s}),g=new Or({depthBuffer:!1}),_=ct[s===q.UNSIGNED_BYTE?`Uint8Array`:`Float32Array`],v=0;v<l;v++){c.mipmaps[v]={pixels:{}},f.material.set(`roughness`,v/(l-1));for(var y=h.width,b=2*Math.atan(y/(y-.5))/Math.PI*180,x=0;x<wi.length;x++){var S=new _(h.width*h.height*4);g.attach(h),g.bind(e);var C=m.getCamera(wi[x]);C.fov=b,e.render(d,C),e.gl.readPixels(0,0,h.width,h.height,q.RGBA,s,S),g.unbind(e),c.mipmaps[v].pixels[wi[x]]=S}h.width/=2,h.height/=2,h.dirty()}return g.dispose(e),h.dispose(e),f.dispose(e),r.dispose(e),{environmentMap:c,brdfLookup:i,normalDistribution:r,maxMipmapLevel:l}},Ci.integrateBRDF=function(e,t){t=t||Ci.generateNormalDistribution();var n=new Or({depthBuffer:!1}),r=new bi({fragment:xi}),i=new J({width:512,height:256,type:q.HALF_FLOAT,wrapS:q.CLAMP_TO_EDGE,wrapT:q.CLAMP_TO_EDGE,minFilter:q.NEAREST,magFilter:q.NEAREST,useMipmap:!1});return r.setUniform(`normalDistribution`,t),r.setUniform(`viewportSize`,[512,256]),r.attachOutput(i),r.render(e,n),n.dispose(e),i},Ci.generateNormalDistribution=function(e,t){for(var e=e||256,t=t||1024,n=new J({width:e,height:t,type:q.FLOAT,minFilter:q.NEAREST,magFilter:q.NEAREST,wrapS:q.CLAMP_TO_EDGE,wrapT:q.CLAMP_TO_EDGE,useMipmap:!1}),r=new Float32Array(t*e*4),i=[],a=0;a<e;a++){for(var o=a/e,s=o*o,c=0;c<t;c++){var l=(c<<16|c>>>16)>>>0;l=((l&1431655765)<<1|(l&2863311530)>>>1)>>>0,l=((l&858993459)<<2|(l&3435973836)>>>2)>>>0,l=((l&252645135)<<4|(l&4042322160)>>>4)>>>0,l=(((l&16711935)<<8|(l&4278255360)>>>8)>>>0)/4294967296;var u=Math.sqrt((1-l)/(1+(s*s-1)*l));i[c]=u}for(var c=0;c<t;c++){var d=(c*e+a)*4,u=i[c],f=Math.sqrt(1-u*u),p=c/t,m=2*Math.PI*p;r[d]=f*Math.cos(m),r[d+1]=u,r[d+2]=f*Math.sin(m),r[d+3]=1}}return n.pixels=r,n};var Ti=Yn.extend({cubemap:null,castShadow:!1,_normalDistribution:null,_brdfLookup:null},{type:`AMBIENT_CUBEMAP_LIGHT`,prefilter:function(e,t){if(!e.getGLExtension(`EXT_shader_texture_lod`)){console.warn(`Device not support textureCubeLodEXT`);return}this._brdfLookup||(this._normalDistribution=Ci.generateNormalDistribution(),this._brdfLookup=Ci.integrateBRDF(e,this._normalDistribution));var n=this.cubemap;if(!n.__prefiltered){var r=Ci.prefilterEnvironmentMap(e,n,{encodeRGBM:!0,width:t,height:t},this._normalDistribution,this._brdfLookup);this.cubemap=r.environmentMap,this.cubemap.__prefiltered=!0,n.dispose(e)}},getBRDFLookup:function(){return this._brdfLookup},uniformTemplates:{ambientCubemapLightColor:{type:`3f`,value:function(e){var t=e.color,n=e.intensity;return[t[0]*n,t[1]*n,t[2]*n]}},ambientCubemapLightCubemap:{type:`t`,value:function(e){return e.cubemap}},ambientCubemapLightBRDFLookup:{type:`t`,value:function(e){return e._brdfLookup}}}}),Ei=Yn.extend({castShadow:!1,coefficients:[]},function(){this._coefficientsTmpArr=new ct.Float32Array(27)},{type:`AMBIENT_SH_LIGHT`,uniformTemplates:{ambientSHLightColor:{type:`3f`,value:function(e){var t=e.color,n=e.intensity;return[t[0]*n,t[1]*n,t[2]*n]}},ambientSHLightCoefficients:{type:`3f`,value:function(e){for(var t=e._coefficientsTmpArr,n=0;n<e.coefficients.length;n++)t[n]=e.coefficients[n];return t}}}}),Di={},Oi=[`px`,`nx`,`py`,`ny`,`pz`,`nz`];function ki(e,t){var n=e[0],r=e[1],i=e[2];return t===0?1:t===1?n:t===2?r:t===3?i:t===4?n*i:t===5?r*i:t===6?n*r:t===7?3*i*i-1:n*n-r*r}var Ai={px:[2,1,0,-1,-1,1],nx:[2,1,0,1,-1,-1],py:[0,2,1,1,-1,-1],ny:[0,2,1,1,1,1],pz:[0,1,2,-1,-1,-1],nz:[0,1,2,1,-1,1]};function ji(e,t,n,r){for(var i=new ct.Float32Array(27),a=I.create(),o=I.create(),s=I.create(),c=0;c<9;c++){for(var l=I.create(),u=0;u<Oi.length;u++){for(var d=t[Oi[u]],f=I.create(),p=0,m=0,h=Ai[Oi[u]],g=0;g<r;g++)for(var _=0;_<n;_++){a[0]=_/(n-1)*2-1,a[1]=g/(r-1)*2-1,a[2]=-1,I.normalize(a,a),s[0]=a[h[0]]*h[3],s[1]=a[h[1]]*h[4],s[2]=a[h[2]]*h[5],o[0]=d[m++]/255,o[1]=d[m++]/255,o[2]=d[m++]/255;var v=d[m++]/255*8.12;o[0]*=v,o[1]*=v,o[2]*=v,I.scaleAndAdd(f,f,o,ki(s,c)*-a[2]),p+=-a[2]}I.scaleAndAdd(l,l,f,1/p)}i[c*3]=l[0]/6,i[c*3+1]=l[1]/6,i[c*3+2]=l[2]/6}return i}Di.projectEnvironmentMap=function(e,t,n){n=n||{},n.lod=n.lod||0;var r,i=new dr,a=64;t.textureType===`texture2D`?r=new Ir({scene:i,environmentMap:t}):(a=t.image&&t.image.px?t.image.px.width:t.width,r=new Fr({scene:i,environmentMap:t}));var o=Math.ceil(a/2**n.lod),s=Math.ceil(a/2**n.lod),c=new J({width:o,height:s}),l=new Or;r.material.define(`fragment`,`RGBM_ENCODE`),n.decodeRGBM&&r.material.define(`fragment`,`RGBM_DECODE`),r.material.set(`lod`,n.lod);for(var u=new Ar({texture:c}),d={},f=0;f<Oi.length;f++){d[Oi[f]]=new Uint8Array(o*s*4);var p=u.getCamera(Oi[f]);p.fov=90,l.attach(c),l.bind(e),e.render(i,p),e.gl.readPixels(0,0,o,s,q.RGBA,q.UNSIGNED_BYTE,d[Oi[f]]),l.unbind(e)}return r.dispose(e),l.dispose(e),c.dispose(e),ji(e,d,o,s)};var X={firstNotNull:function(){for(var e=0,t=arguments.length;e<t;e++)if(arguments[e]!=null)return arguments[e]},queryDataIndex:function(e,t){if(t.dataIndexInside!=null)return t.dataIndexInside;if(t.dataIndex!=null)return F(t.dataIndex)?ae(t.dataIndex,function(t){return e.indexOfRawIndex(t)}):e.indexOfRawIndex(t.dataIndex);if(t.name!=null)return F(t.name)?ae(t.name,function(t){return e.indexOfName(t)}):e.indexOfName(t.name)}},Mi=Y.extend({dynamic:!1,widthSegments:40,heightSegments:20,phiStart:0,phiLength:Math.PI*2,thetaStart:0,thetaLength:Math.PI,radius:1},function(){this.build()},{build:function(){var e=this.heightSegments,t=this.widthSegments,n=this.attributes.position,r=this.attributes.texcoord0,i=this.attributes.normal,a=(t+1)*(e+1);n.init(a),r.init(a),i.init(a);var o=a>65535?Uint32Array:Uint16Array,s=this.indices=new o(t*e*6),c,l,u,d,f,p,m,h=this.radius,g=this.phiStart,_=this.phiLength,v=this.thetaStart,y=this.thetaLength,h=this.radius,b=[],x=[],S=0,C=1/h;for(m=0;m<=e;m++)for(p=0;p<=t;p++)d=p/t,f=m/e,c=-h*Math.cos(g+d*_)*Math.sin(v+f*y),l=h*Math.cos(v+f*y),u=h*Math.sin(g+d*_)*Math.sin(v+f*y),b[0]=c,b[1]=l,b[2]=u,x[0]=d,x[1]=f,n.set(S,b),r.set(S,x),b[0]*=C,b[1]*=C,b[2]*=C,i.set(S,b),S++;var w,T,E,D,O=t+1,k=0;for(m=0;m<e;m++)for(p=0;p<t;p++)T=m*O+p,w=m*O+p+1,D=(m+1)*O+p+1,E=(m+1)*O+p,s[k++]=w,s[k++]=T,s[k++]=D,s[k++]=T,s[k++]=E,s[k++]=D;this.boundingBox=new Ze,this.boundingBox.max.set(h,h,h),this.boundingBox.min.set(-h,-h,-h)}}),Ni=Yn.extend({castShadow:!1},{type:`AMBIENT_LIGHT`,uniformTemplates:{ambientLightColor:{type:`3f`,value:function(e){var t=e.color,n=e.intensity;return[t[0]*n,t[1]*n,t[2]*n]}}}}),Pi=Yn.extend({shadowBias:.001,shadowSlopeScale:2,shadowCascade:1,cascadeSplitLogFactor:.2},{type:`DIRECTIONAL_LIGHT`,uniformTemplates:{directionalLightDirection:{type:`3f`,value:function(e){return e.__dir=e.__dir||new L,e.__dir.copy(e.worldTransform.z).normalize().negate().array}},directionalLightColor:{type:`3f`,value:function(e){var t=e.color,n=e.intensity;return[t[0]*n,t[1]*n,t[2]*n]}}},clone:function(){var e=Yn.prototype.clone.call(this);return e.shadowBias=this.shadowBias,e.shadowSlopeScale=this.shadowSlopeScale,e}}),Fi=Yn.extend({range:100,castShadow:!1},{type:`POINT_LIGHT`,uniformTemplates:{pointLightPosition:{type:`3f`,value:function(e){return e.getWorldPosition().array}},pointLightRange:{type:`1f`,value:function(e){return e.range}},pointLightColor:{type:`3f`,value:function(e){var t=e.color,n=e.intensity;return[t[0]*n,t[1]*n,t[2]*n]}}},clone:function(){var e=Yn.prototype.clone.call(this);return e.range=this.range,e}}),Ii=Yn.extend({range:20,umbraAngle:30,penumbraAngle:45,falloffFactor:2,shadowBias:.001,shadowSlopeScale:2},{type:`SPOT_LIGHT`,uniformTemplates:{spotLightPosition:{type:`3f`,value:function(e){return e.getWorldPosition().array}},spotLightRange:{type:`1f`,value:function(e){return e.range}},spotLightUmbraAngleCosine:{type:`1f`,value:function(e){return Math.cos(e.umbraAngle*Math.PI/180)}},spotLightPenumbraAngleCosine:{type:`1f`,value:function(e){return Math.cos(e.penumbraAngle*Math.PI/180)}},spotLightFalloffFactor:{type:`1f`,value:function(e){return e.falloffFactor}},spotLightDirection:{type:`3f`,value:function(e){return e.__dir=e.__dir||new L,e.__dir.copy(e.worldTransform.z).negate().array}},spotLightColor:{type:`3f`,value:function(e){var t=e.color,n=e.intensity;return[t[0]*n,t[1]*n,t[2]*n]}}},clone:function(){var e=Yn.prototype.clone.call(this);return e.range=this.range,e.umbraAngle=this.umbraAngle,e.penumbraAngle=this.penumbraAngle,e.falloffFactor=this.falloffFactor,e.shadowBias=this.shadowBias,e.shadowSlopeScale=this.shadowSlopeScale,e}}),Li=function(e,t,n,r){e=e||0,t=t||0,n=n||0,r=r||0,this.array=R.fromValues(e,t,n,r),this._dirty=!0};Li.prototype={constructor:Li,add:function(e){return R.add(this.array,this.array,e.array),this._dirty=!0,this},set:function(e,t,n,r){return this.array[0]=e,this.array[1]=t,this.array[2]=n,this.array[3]=r,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this.array[2]=e[2],this.array[3]=e[3],this._dirty=!0,this},clone:function(){return new Li(this.x,this.y,this.z,this.w)},copy:function(e){return R.copy(this.array,e.array),this._dirty=!0,this},dist:function(e){return R.dist(this.array,e.array)},distance:function(e){return R.distance(this.array,e.array)},div:function(e){return R.div(this.array,this.array,e.array),this._dirty=!0,this},divide:function(e){return R.divide(this.array,this.array,e.array),this._dirty=!0,this},dot:function(e){return R.dot(this.array,e.array)},len:function(){return R.len(this.array)},length:function(){return R.length(this.array)},lerp:function(e,t,n){return R.lerp(this.array,e.array,t.array,n),this._dirty=!0,this},min:function(e){return R.min(this.array,this.array,e.array),this._dirty=!0,this},max:function(e){return R.max(this.array,this.array,e.array),this._dirty=!0,this},mul:function(e){return R.mul(this.array,this.array,e.array),this._dirty=!0,this},multiply:function(e){return R.multiply(this.array,this.array,e.array),this._dirty=!0,this},negate:function(){return R.negate(this.array,this.array),this._dirty=!0,this},normalize:function(){return R.normalize(this.array,this.array),this._dirty=!0,this},random:function(e){return R.random(this.array,e),this._dirty=!0,this},scale:function(e){return R.scale(this.array,this.array,e),this._dirty=!0,this},scaleAndAdd:function(e,t){return R.scaleAndAdd(this.array,this.array,e.array,t),this._dirty=!0,this},sqrDist:function(e){return R.sqrDist(this.array,e.array)},squaredDistance:function(e){return R.squaredDistance(this.array,e.array)},sqrLen:function(){return R.sqrLen(this.array)},squaredLength:function(){return R.squaredLength(this.array)},sub:function(e){return R.sub(this.array,this.array,e.array),this._dirty=!0,this},subtract:function(e){return R.subtract(this.array,this.array,e.array),this._dirty=!0,this},transformMat4:function(e){return R.transformMat4(this.array,this.array,e.array),this._dirty=!0,this},transformQuat:function(e){return R.transformQuat(this.array,this.array,e.array),this._dirty=!0,this},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}};var Ri=Object.defineProperty;if(Ri){var zi=Li.prototype;Ri(zi,`x`,{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),Ri(zi,`y`,{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}}),Ri(zi,`z`,{get:function(){return this.array[2]},set:function(e){this.array[2]=e,this._dirty=!0}}),Ri(zi,`w`,{get:function(){return this.array[3]},set:function(e){this.array[3]=e,this._dirty=!0}})}Li.add=function(e,t,n){return R.add(e.array,t.array,n.array),e._dirty=!0,e},Li.set=function(e,t,n,r,i){R.set(e.array,t,n,r,i),e._dirty=!0},Li.copy=function(e,t){return R.copy(e.array,t.array),e._dirty=!0,e},Li.dist=function(e,t){return R.distance(e.array,t.array)},Li.distance=Li.dist,Li.div=function(e,t,n){return R.divide(e.array,t.array,n.array),e._dirty=!0,e},Li.divide=Li.div,Li.dot=function(e,t){return R.dot(e.array,t.array)},Li.len=function(e){return R.length(e.array)},Li.lerp=function(e,t,n,r){return R.lerp(e.array,t.array,n.array,r),e._dirty=!0,e},Li.min=function(e,t,n){return R.min(e.array,t.array,n.array),e._dirty=!0,e},Li.max=function(e,t,n){return R.max(e.array,t.array,n.array),e._dirty=!0,e},Li.mul=function(e,t,n){return R.multiply(e.array,t.array,n.array),e._dirty=!0,e},Li.multiply=Li.mul,Li.negate=function(e,t){return R.negate(e.array,t.array),e._dirty=!0,e},Li.normalize=function(e,t){return R.normalize(e.array,t.array),e._dirty=!0,e},Li.random=function(e,t){return R.random(e.array,t),e._dirty=!0,e},Li.scale=function(e,t,n){return R.scale(e.array,t.array,n),e._dirty=!0,e},Li.scaleAndAdd=function(e,t,n,r){return R.scaleAndAdd(e.array,t.array,n.array,r),e._dirty=!0,e},Li.sqrDist=function(e,t){return R.sqrDist(e.array,t.array)},Li.squaredDistance=Li.sqrDist,Li.sqrLen=function(e){return R.sqrLen(e.array)},Li.squaredLength=Li.sqrLen,Li.sub=function(e,t,n){return R.subtract(e.array,t.array,n.array),e._dirty=!0,e},Li.subtract=Li.sub,Li.transformMat4=function(e,t,n){return R.transformMat4(e.array,t.array,n.array),e._dirty=!0,e},Li.transformQuat=function(e,t,n){return R.transformQuat(e.array,t.array,n.array),e._dirty=!0,e};var Z={};Z.create=function(){var e=new Ie(4);return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e},Z.clone=function(e){var t=new Ie(4);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t},Z.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e},Z.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e},Z.transpose=function(e,t){if(e===t){var n=t[1];e[1]=t[2],e[2]=n}else e[0]=t[0],e[1]=t[2],e[2]=t[1],e[3]=t[3];return e},Z.invert=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=n*a-i*r;return o?(o=1/o,e[0]=a*o,e[1]=-r*o,e[2]=-i*o,e[3]=n*o,e):null},Z.adjoint=function(e,t){var n=t[0];return e[0]=t[3],e[1]=-t[1],e[2]=-t[2],e[3]=n,e},Z.determinant=function(e){return e[0]*e[3]-e[2]*e[1]},Z.multiply=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=n[0],c=n[1],l=n[2],u=n[3];return e[0]=r*s+a*c,e[1]=i*s+o*c,e[2]=r*l+a*u,e[3]=i*l+o*u,e},Z.mul=Z.multiply,Z.rotate=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=Math.sin(n),c=Math.cos(n);return e[0]=r*c+a*s,e[1]=i*c+o*s,e[2]=r*-s+a*c,e[3]=i*-s+o*c,e},Z.scale=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=n[0],c=n[1];return e[0]=r*s,e[1]=i*s,e[2]=a*c,e[3]=o*c,e},Z.frob=function(e){return Math.sqrt(e[0]**2+e[1]**2+e[2]**2+e[3]**2)},Z.LDU=function(e,t,n,r){return e[2]=r[2]/r[0],n[0]=r[0],n[1]=r[1],n[3]=r[3]-e[2]*n[1],[e,t,n]};var Bi=function(){this.array=Z.create(),this._dirty=!0};Bi.prototype={constructor:Bi,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},clone:function(){return new Bi().copy(this)},copy:function(e){return Z.copy(this.array,e.array),this._dirty=!0,this},adjoint:function(){return Z.adjoint(this.array,this.array),this._dirty=!0,this},determinant:function(){return Z.determinant(this.array)},identity:function(){return Z.identity(this.array),this._dirty=!0,this},invert:function(){return Z.invert(this.array,this.array),this._dirty=!0,this},mul:function(e){return Z.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return Z.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return Z.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return Z.multiply(this.array,e.array,this.array),this._dirty=!0,this},rotate:function(e){return Z.rotate(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return Z.scale(this.array,this.array,e.array),this._dirty=!0,this},transpose:function(){return Z.transpose(this.array,this.array),this._dirty=!0,this},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}},Bi.adjoint=function(e,t){return Z.adjoint(e.array,t.array),e._dirty=!0,e},Bi.copy=function(e,t){return Z.copy(e.array,t.array),e._dirty=!0,e},Bi.determinant=function(e){return Z.determinant(e.array)},Bi.identity=function(e){return Z.identity(e.array),e._dirty=!0,e},Bi.invert=function(e,t){return Z.invert(e.array,t.array),e._dirty=!0,e},Bi.mul=function(e,t,n){return Z.mul(e.array,t.array,n.array),e._dirty=!0,e},Bi.multiply=Bi.mul,Bi.rotate=function(e,t,n){return Z.rotate(e.array,t.array,n),e._dirty=!0,e},Bi.scale=function(e,t,n){return Z.scale(e.array,t.array,n.array),e._dirty=!0,e},Bi.transpose=function(e,t){return Z.transpose(e.array,t.array),e._dirty=!0,e};var Vi={};Vi.create=function(){var e=new Ie(6);return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e[4]=0,e[5]=0,e},Vi.clone=function(e){var t=new Ie(6);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t[4]=e[4],t[5]=e[5],t},Vi.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e},Vi.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e[4]=0,e[5]=0,e},Vi.invert=function(e,t){var n=t[0],r=t[1],i=t[2],a=t[3],o=t[4],s=t[5],c=n*a-r*i;return c?(c=1/c,e[0]=a*c,e[1]=-r*c,e[2]=-i*c,e[3]=n*c,e[4]=(i*s-a*o)*c,e[5]=(r*o-n*s)*c,e):null},Vi.determinant=function(e){return e[0]*e[3]-e[1]*e[2]},Vi.multiply=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=n[0],u=n[1],d=n[2],f=n[3],p=n[4],m=n[5];return e[0]=r*l+a*u,e[1]=i*l+o*u,e[2]=r*d+a*f,e[3]=i*d+o*f,e[4]=r*p+a*m+s,e[5]=i*p+o*m+c,e},Vi.mul=Vi.multiply,Vi.rotate=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=Math.sin(n),u=Math.cos(n);return e[0]=r*u+a*l,e[1]=i*u+o*l,e[2]=r*-l+a*u,e[3]=i*-l+o*u,e[4]=s,e[5]=c,e},Vi.scale=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=n[0],u=n[1];return e[0]=r*l,e[1]=i*l,e[2]=a*u,e[3]=o*u,e[4]=s,e[5]=c,e},Vi.translate=function(e,t,n){var r=t[0],i=t[1],a=t[2],o=t[3],s=t[4],c=t[5],l=n[0],u=n[1];return e[0]=r,e[1]=i,e[2]=a,e[3]=o,e[4]=r*l+a*u+s,e[5]=i*l+o*u+c,e},Vi.frob=function(e){return Math.sqrt(e[0]**2+e[1]**2+e[2]**2+e[3]**2+e[4]**2+e[5]**2+1)};var Hi=function(){this.array=Vi.create(),this._dirty=!0};Hi.prototype={constructor:Hi,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},clone:function(){return new Hi().copy(this)},copy:function(e){return Vi.copy(this.array,e.array),this._dirty=!0,this},determinant:function(){return Vi.determinant(this.array)},identity:function(){return Vi.identity(this.array),this._dirty=!0,this},invert:function(){return Vi.invert(this.array,this.array),this._dirty=!0,this},mul:function(e){return Vi.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return Vi.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return Vi.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return Vi.multiply(this.array,e.array,this.array),this._dirty=!0,this},rotate:function(e){return Vi.rotate(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return Vi.scale(this.array,this.array,e.array),this._dirty=!0,this},translate:function(e){return Vi.translate(this.array,this.array,e.array),this._dirty=!0,this},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}},Hi.copy=function(e,t){return Vi.copy(e.array,t.array),e._dirty=!0,e},Hi.determinant=function(e){return Vi.determinant(e.array)},Hi.identity=function(e){return Vi.identity(e.array),e._dirty=!0,e},Hi.invert=function(e,t){return Vi.invert(e.array,t.array),e._dirty=!0,e},Hi.mul=function(e,t,n){return Vi.mul(e.array,t.array,n.array),e._dirty=!0,e},Hi.multiply=Hi.mul,Hi.rotate=function(e,t,n){return Vi.rotate(e.array,t.array,n),e._dirty=!0,e},Hi.scale=function(e,t,n){return Vi.scale(e.array,t.array,n.array),e._dirty=!0,e},Hi.translate=function(e,t,n){return Vi.translate(e.array,t.array,n.array),e._dirty=!0,e};var Ui=function(){this.array=z.create(),this._dirty=!0};Ui.prototype={constructor:Ui,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},adjoint:function(){return z.adjoint(this.array,this.array),this._dirty=!0,this},clone:function(){return new Ui().copy(this)},copy:function(e){return z.copy(this.array,e.array),this._dirty=!0,this},determinant:function(){return z.determinant(this.array)},fromMat2d:function(e){return z.fromMat2d(this.array,e.array),this._dirty=!0,this},fromMat4:function(e){return z.fromMat4(this.array,e.array),this._dirty=!0,this},fromQuat:function(e){return z.fromQuat(this.array,e.array),this._dirty=!0,this},identity:function(){return z.identity(this.array),this._dirty=!0,this},invert:function(){return z.invert(this.array,this.array),this._dirty=!0,this},mul:function(e){return z.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return z.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return z.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return z.multiply(this.array,e.array,this.array),this._dirty=!0,this},rotate:function(e){return z.rotate(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return z.scale(this.array,this.array,e.array),this._dirty=!0,this},translate:function(e){return z.translate(this.array,this.array,e.array),this._dirty=!0,this},normalFromMat4:function(e){return z.normalFromMat4(this.array,e.array),this._dirty=!0,this},transpose:function(){return z.transpose(this.array,this.array),this._dirty=!0,this},toString:function(){return`[`+Array.prototype.join.call(this.array,`,`)+`]`},toArray:function(){return Array.prototype.slice.call(this.array)}},Ui.adjoint=function(e,t){return z.adjoint(e.array,t.array),e._dirty=!0,e},Ui.copy=function(e,t){return z.copy(e.array,t.array),e._dirty=!0,e},Ui.determinant=function(e){return z.determinant(e.array)},Ui.identity=function(e){return z.identity(e.array),e._dirty=!0,e},Ui.invert=function(e,t){return z.invert(e.array,t.array),e},Ui.mul=function(e,t,n){return z.mul(e.array,t.array,n.array),e._dirty=!0,e},Ui.multiply=Ui.mul,Ui.fromMat2d=function(e,t){return z.fromMat2d(e.array,t.array),e._dirty=!0,e},Ui.fromMat4=function(e,t){return z.fromMat4(e.array,t.array),e._dirty=!0,e},Ui.fromQuat=function(e,t){return z.fromQuat(e.array,t.array),e._dirty=!0,e},Ui.normalFromMat4=function(e,t){return z.normalFromMat4(e.array,t.array),e._dirty=!0,e},Ui.rotate=function(e,t,n){return z.rotate(e.array,t.array,n),e._dirty=!0,e},Ui.scale=function(e,t,n){return z.scale(e.array,t.array,n.array),e._dirty=!0,e},Ui.transpose=function(e,t){return z.transpose(e.array,t.array),e._dirty=!0,e},Ui.translate=function(e,t,n){return z.translate(e.array,t.array,n.array),e._dirty=!0,e};var Wi={_animators:null,getAnimators:function(){return this._animators=this._animators||[],this._animators},animate:function(e,t){this._animators=this._animators||[];var n=this,r;if(e){for(var i=e.split(`.`),a=n,o=0,s=i.length;o<s;o++)a&&(a=a[i[o]]);a&&(r=a)}else r=n;if(r==null)throw Error(`Target `+e+` not exists`);var c=this._animators,l=new te(r,t),u=this;return l.during(function(){u.__zr&&u.__zr.refresh()}).done(function(){var e=c.indexOf(l);e>=0&&c.splice(e,1)}),c.push(l),this.__zr&&this.__zr.animation.addAnimator(l),l},stopAnimation:function(e){this._animators=this._animators||[];for(var t=this._animators,n=t.length,r=0;r<n;r++)t[r].stop(e);return t.length=0,this},addAnimatorsToZr:function(e){if(this._animators)for(var t=0;t<this._animators.length;t++)e.animation.addAnimator(this._animators[t])},removeAnimatorsFromZr:function(e){if(this._animators)for(var t=0;t<this._animators.length;t++)e.animation.removeAnimator(this._animators[t])}},Gi=`
@export clay.util.rand
highp float rand(vec2 uv) {
 const highp float a = 12.9898, b = 78.233, c = 43758.5453;
 highp float dt = dot(uv.xy, vec2(a,b)), sn = mod(dt, 3.141592653589793);
 return fract(sin(sn) * c);
}
@end
@export clay.util.calculate_attenuation
uniform float attenuationFactor : 5.0;
float lightAttenuation(float dist, float range)
{
 float attenuation = 1.0;
 attenuation = dist*dist/(range*range+1.0);
 float att_s = attenuationFactor;
 attenuation = 1.0/(attenuation*att_s+1.0);
 att_s = 1.0/(att_s+1.0);
 attenuation = attenuation - att_s;
 attenuation /= 1.0 - att_s;
 return clamp(attenuation, 0.0, 1.0);
}
@end
@export clay.util.edge_factor
#ifdef SUPPORT_STANDARD_DERIVATIVES
float edgeFactor(float width)
{
 vec3 d = fwidth(v_Barycentric);
 vec3 a3 = smoothstep(vec3(0.0), d * width, v_Barycentric);
 return min(min(a3.x, a3.y), a3.z);
}
#else
float edgeFactor(float width)
{
 return 1.0;
}
#endif
@end
@export clay.util.encode_float
vec4 encodeFloat(const in float depth)
{
 const vec4 bitShifts = vec4(256.0*256.0*256.0, 256.0*256.0, 256.0, 1.0);
 const vec4 bit_mask = vec4(0.0, 1.0/256.0, 1.0/256.0, 1.0/256.0);
 vec4 res = fract(depth * bitShifts);
 res -= res.xxyz * bit_mask;
 return res;
}
@end
@export clay.util.decode_float
float decodeFloat(const in vec4 color)
{
 const vec4 bitShifts = vec4(1.0/(256.0*256.0*256.0), 1.0/(256.0*256.0), 1.0/256.0, 1.0);
 return dot(color, bitShifts);
}
@end
@export clay.util.float
@import clay.util.encode_float
@import clay.util.decode_float
@end
@export clay.util.rgbm_decode
vec3 RGBMDecode(vec4 rgbm, float range) {
 return range * rgbm.rgb * rgbm.a;
}
@end
@export clay.util.rgbm_encode
vec4 RGBMEncode(vec3 color, float range) {
 if (dot(color, color) == 0.0) {
 return vec4(0.0);
 }
 vec4 rgbm;
 color /= range;
 rgbm.a = clamp(max(max(color.r, color.g), max(color.b, 1e-6)), 0.0, 1.0);
 rgbm.a = ceil(rgbm.a * 255.0) / 255.0;
 rgbm.rgb = color / rgbm.a;
 return rgbm;
}
@end
@export clay.util.rgbm
@import clay.util.rgbm_decode
@import clay.util.rgbm_encode
vec4 decodeHDR(vec4 color)
{
#if defined(RGBM_DECODE) || defined(RGBM)
 return vec4(RGBMDecode(color, 8.12), 1.0);
#else
 return color;
#endif
}
vec4 encodeHDR(vec4 color)
{
#if defined(RGBM_ENCODE) || defined(RGBM)
 return RGBMEncode(color.xyz, 8.12);
#else
 return color;
#endif
}
@end
@export clay.util.srgb
vec4 sRGBToLinear(in vec4 value) {
 return vec4(mix(pow(value.rgb * 0.9478672986 + vec3(0.0521327014), vec3(2.4)), value.rgb * 0.0773993808, vec3(lessThanEqual(value.rgb, vec3(0.04045)))), value.w);
}
vec4 linearTosRGB(in vec4 value) {
 return vec4(mix(pow(value.rgb, vec3(0.41666)) * 1.055 - vec3(0.055), value.rgb * 12.92, vec3(lessThanEqual(value.rgb, vec3(0.0031308)))), value.w);
}
@end
@export clay.chunk.skinning_header
#ifdef SKINNING
attribute vec3 weight : WEIGHT;
attribute vec4 joint : JOINT;
#ifdef USE_SKIN_MATRICES_TEXTURE
uniform sampler2D skinMatricesTexture : ignore;
uniform float skinMatricesTextureSize: ignore;
mat4 getSkinMatrix(sampler2D tex, float idx) {
 float j = idx * 4.0;
 float x = mod(j, skinMatricesTextureSize);
 float y = floor(j / skinMatricesTextureSize) + 0.5;
 vec2 scale = vec2(skinMatricesTextureSize);
 return mat4(
 texture2D(tex, vec2(x + 0.5, y) / scale),
 texture2D(tex, vec2(x + 1.5, y) / scale),
 texture2D(tex, vec2(x + 2.5, y) / scale),
 texture2D(tex, vec2(x + 3.5, y) / scale)
 );
}
mat4 getSkinMatrix(float idx) {
 return getSkinMatrix(skinMatricesTexture, idx);
}
#else
uniform mat4 skinMatrix[JOINT_COUNT] : SKIN_MATRIX;
mat4 getSkinMatrix(float idx) {
 return skinMatrix[int(idx)];
}
#endif
#endif
@end
@export clay.chunk.skin_matrix
mat4 skinMatrixWS = getSkinMatrix(joint.x) * weight.x;
if (weight.y > 1e-4)
{
 skinMatrixWS += getSkinMatrix(joint.y) * weight.y;
}
if (weight.z > 1e-4)
{
 skinMatrixWS += getSkinMatrix(joint.z) * weight.z;
}
float weightW = 1.0-weight.x-weight.y-weight.z;
if (weightW > 1e-4)
{
 skinMatrixWS += getSkinMatrix(joint.w) * weightW;
}
@end
@export clay.chunk.instancing_header
#ifdef INSTANCING
attribute vec4 instanceMat1;
attribute vec4 instanceMat2;
attribute vec4 instanceMat3;
#endif
@end
@export clay.chunk.instancing_matrix
mat4 instanceMat = mat4(
 vec4(instanceMat1.xyz, 0.0),
 vec4(instanceMat2.xyz, 0.0),
 vec4(instanceMat3.xyz, 0.0),
 vec4(instanceMat1.w, instanceMat2.w, instanceMat3.w, 1.0)
);
@end
@export clay.util.parallax_correct
vec3 parallaxCorrect(in vec3 dir, in vec3 pos, in vec3 boxMin, in vec3 boxMax) {
 vec3 first = (boxMax - pos) / dir;
 vec3 second = (boxMin - pos) / dir;
 vec3 further = max(first, second);
 float dist = min(further.x, min(further.y, further.z));
 vec3 fixedPos = pos + dir * dist;
 vec3 boxCenter = (boxMax + boxMin) * 0.5;
 return normalize(fixedPos - boxCenter);
}
@end
@export clay.util.clamp_sample
vec4 clampSample(const in sampler2D texture, const in vec2 coord)
{
#ifdef STEREO
 float eye = step(0.5, coord.x) * 0.5;
 vec2 coordClamped = clamp(coord, vec2(eye, 0.0), vec2(0.5 + eye, 1.0));
#else
 vec2 coordClamped = clamp(coord, vec2(0.0), vec2(1.0));
#endif
 return texture2D(texture, coordClamped);
}
@end
@export clay.util.ACES
vec3 ACESToneMapping(vec3 color)
{
 const float A = 2.51;
 const float B = 0.03;
 const float C = 2.43;
 const float D = 0.59;
 const float E = 0.14;
 return (color * (A * color + B)) / (color * (C * color + D) + E);
}
@end`;Object.assign($e.prototype,Wi),K.import(Gi),K.import(pn),K.import(`
@export ecgl.common.transformUniforms
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform mat4 worldInverseTranspose : WORLDINVERSETRANSPOSE;
uniform mat4 world : WORLD;
@end

@export ecgl.common.attributes
attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;
attribute vec3 normal : NORMAL;
@end

@export ecgl.common.uv.header
uniform vec2 uvRepeat : [1.0, 1.0];
uniform vec2 uvOffset : [0.0, 0.0];
uniform vec2 detailUvRepeat : [1.0, 1.0];
uniform vec2 detailUvOffset : [0.0, 0.0];

varying vec2 v_Texcoord;
varying vec2 v_DetailTexcoord;
@end

@export ecgl.common.uv.main
v_Texcoord = texcoord * uvRepeat + uvOffset;
v_DetailTexcoord = texcoord * detailUvRepeat + detailUvOffset;
@end

@export ecgl.common.uv.fragmentHeader
varying vec2 v_Texcoord;
varying vec2 v_DetailTexcoord;
@end


@export ecgl.common.albedo.main

 vec4 albedoTexel = vec4(1.0);
#ifdef DIFFUSEMAP_ENABLED
 albedoTexel = texture2D(diffuseMap, v_Texcoord);
 #ifdef SRGB_DECODE
 albedoTexel = sRGBToLinear(albedoTexel);
 #endif
#endif

#ifdef DETAILMAP_ENABLED
 vec4 detailTexel = texture2D(detailMap, v_DetailTexcoord);
 #ifdef SRGB_DECODE
 detailTexel = sRGBToLinear(detailTexel);
 #endif
 albedoTexel.rgb = mix(albedoTexel.rgb, detailTexel.rgb, detailTexel.a);
 albedoTexel.a = detailTexel.a + (1.0 - detailTexel.a) * albedoTexel.a;
#endif

@end

@export ecgl.common.wireframe.vertexHeader

#ifdef WIREFRAME_QUAD
attribute vec4 barycentric;
varying vec4 v_Barycentric;
#elif defined(WIREFRAME_TRIANGLE)
attribute vec3 barycentric;
varying vec3 v_Barycentric;
#endif

@end

@export ecgl.common.wireframe.vertexMain

#if defined(WIREFRAME_QUAD) || defined(WIREFRAME_TRIANGLE)
 v_Barycentric = barycentric;
#endif

@end


@export ecgl.common.wireframe.fragmentHeader

uniform float wireframeLineWidth : 1;
uniform vec4 wireframeLineColor: [0, 0, 0, 0.5];

#ifdef WIREFRAME_QUAD
varying vec4 v_Barycentric;
float edgeFactor () {
 vec4 d = fwidth(v_Barycentric);
 vec4 a4 = smoothstep(vec4(0.0), d * wireframeLineWidth, v_Barycentric);
 return min(min(min(a4.x, a4.y), a4.z), a4.w);
}
#elif defined(WIREFRAME_TRIANGLE)
varying vec3 v_Barycentric;
float edgeFactor () {
 vec3 d = fwidth(v_Barycentric);
 vec3 a3 = smoothstep(vec3(0.0), d * wireframeLineWidth, v_Barycentric);
 return min(min(a3.x, a3.y), a3.z);
}
#endif

@end


@export ecgl.common.wireframe.fragmentMain

#if defined(WIREFRAME_QUAD) || defined(WIREFRAME_TRIANGLE)
 if (wireframeLineWidth > 0.) {
 vec4 lineColor = wireframeLineColor;
#ifdef SRGB_DECODE
 lineColor = sRGBToLinear(lineColor);
#endif

 gl_FragColor.rgb = mix(gl_FragColor.rgb, lineColor.rgb, (1.0 - edgeFactor()) * lineColor.a);
 }
#endif
@end




@export ecgl.common.bumpMap.header

#ifdef BUMPMAP_ENABLED
uniform sampler2D bumpMap;
uniform float bumpScale : 1.0;


vec3 bumpNormal(vec3 surfPos, vec3 surfNormal, vec3 baseNormal)
{
 vec2 dSTdx = dFdx(v_Texcoord);
 vec2 dSTdy = dFdy(v_Texcoord);

 float Hll = bumpScale * texture2D(bumpMap, v_Texcoord).x;
 float dHx = bumpScale * texture2D(bumpMap, v_Texcoord + dSTdx).x - Hll;
 float dHy = bumpScale * texture2D(bumpMap, v_Texcoord + dSTdy).x - Hll;

 vec3 vSigmaX = dFdx(surfPos);
 vec3 vSigmaY = dFdy(surfPos);
 vec3 vN = surfNormal;

 vec3 R1 = cross(vSigmaY, vN);
 vec3 R2 = cross(vN, vSigmaX);

 float fDet = dot(vSigmaX, R1);

 vec3 vGrad = sign(fDet) * (dHx * R1 + dHy * R2);
 return normalize(abs(fDet) * baseNormal - vGrad);

}
#endif

@end

@export ecgl.common.normalMap.vertexHeader

#ifdef NORMALMAP_ENABLED
attribute vec4 tangent : TANGENT;
varying vec3 v_Tangent;
varying vec3 v_Bitangent;
#endif

@end

@export ecgl.common.normalMap.vertexMain

#ifdef NORMALMAP_ENABLED
 if (dot(tangent, tangent) > 0.0) {
 v_Tangent = normalize((worldInverseTranspose * vec4(tangent.xyz, 0.0)).xyz);
 v_Bitangent = normalize(cross(v_Normal, v_Tangent) * tangent.w);
 }
#endif

@end


@export ecgl.common.normalMap.fragmentHeader

#ifdef NORMALMAP_ENABLED
uniform sampler2D normalMap;
varying vec3 v_Tangent;
varying vec3 v_Bitangent;
#endif

@end

@export ecgl.common.normalMap.fragmentMain
#ifdef NORMALMAP_ENABLED
 if (dot(v_Tangent, v_Tangent) > 0.0) {
 vec3 normalTexel = texture2D(normalMap, v_DetailTexcoord).xyz;
 if (dot(normalTexel, normalTexel) > 0.0) { N = normalTexel * 2.0 - 1.0;
 mat3 tbn = mat3(v_Tangent, v_Bitangent, v_Normal);
 N = normalize(tbn * N);
 }
 }
#endif
@end



@export ecgl.common.vertexAnimation.header

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
attribute vec3 prevNormal;
uniform float percent;
#endif

@end

@export ecgl.common.vertexAnimation.main

#ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
 vec3 norm = mix(prevNormal, normal, percent);
#else
 vec3 pos = position;
 vec3 norm = normal;
#endif

@end


@export ecgl.common.ssaoMap.header
#ifdef SSAOMAP_ENABLED
uniform sampler2D ssaoMap;
uniform vec4 viewport : VIEWPORT;
#endif
@end

@export ecgl.common.ssaoMap.main
 float ao = 1.0;
#ifdef SSAOMAP_ENABLED
 ao = texture2D(ssaoMap, (gl_FragCoord.xy - viewport.xy) / viewport.zw).r;
#endif
@end




@export ecgl.common.diffuseLayer.header

#if (LAYER_DIFFUSEMAP_COUNT > 0)
uniform float layerDiffuseIntensity[LAYER_DIFFUSEMAP_COUNT];
uniform sampler2D layerDiffuseMap[LAYER_DIFFUSEMAP_COUNT];
#endif

@end

@export ecgl.common.emissiveLayer.header

#if (LAYER_EMISSIVEMAP_COUNT > 0)
uniform float layerEmissionIntensity[LAYER_EMISSIVEMAP_COUNT];
uniform sampler2D layerEmissiveMap[LAYER_EMISSIVEMAP_COUNT];
#endif

@end

@export ecgl.common.layers.header
@import ecgl.common.diffuseLayer.header
@import ecgl.common.emissiveLayer.header
@end

@export ecgl.common.diffuseLayer.main

#if (LAYER_DIFFUSEMAP_COUNT > 0)
 for (int _idx_ = 0; _idx_ < LAYER_DIFFUSEMAP_COUNT; _idx_++) {{
 float intensity = layerDiffuseIntensity[_idx_];
 vec4 texel2 = texture2D(layerDiffuseMap[_idx_], v_Texcoord);
 #ifdef SRGB_DECODE
 texel2 = sRGBToLinear(texel2);
 #endif
 albedoTexel.rgb = mix(albedoTexel.rgb, texel2.rgb * intensity, texel2.a);
 albedoTexel.a = texel2.a + (1.0 - texel2.a) * albedoTexel.a;
 }}
#endif

@end

@export ecgl.common.emissiveLayer.main

#if (LAYER_EMISSIVEMAP_COUNT > 0)
 for (int _idx_ = 0; _idx_ < LAYER_EMISSIVEMAP_COUNT; _idx_++)
 {{
 vec4 texel2 = texture2D(layerEmissiveMap[_idx_], v_Texcoord) * layerEmissionIntensity[_idx_];
 #ifdef SRGB_DECODE
 texel2 = sRGBToLinear(texel2);
 #endif
 float intensity = layerEmissionIntensity[_idx_];
 gl_FragColor.rgb += texel2.rgb * texel2.a * intensity;
 }}
#endif

@end
`),K.import(`@export ecgl.color.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

@import ecgl.common.uv.header

attribute vec2 texcoord : TEXCOORD_0;
attribute vec3 position: POSITION;

@import ecgl.common.wireframe.vertexHeader

#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
uniform float percent : 1.0;
#endif

#ifdef ATMOSPHERE_ENABLED
attribute vec3 normal: NORMAL;
uniform mat4 worldInverseTranspose : WORLDINVERSETRANSPOSE;
varying vec3 v_Normal;
#endif

void main()
{
#ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
#else
 vec3 pos = position;
#endif

 gl_Position = worldViewProjection * vec4(pos, 1.0);

 @import ecgl.common.uv.main

#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif

#ifdef ATMOSPHERE_ENABLED
 v_Normal = normalize((worldInverseTranspose * vec4(normal, 0.0)).xyz);
#endif

 @import ecgl.common.wireframe.vertexMain

}

@end

@export ecgl.color.fragment

#define LAYER_DIFFUSEMAP_COUNT 0
#define LAYER_EMISSIVEMAP_COUNT 0

uniform sampler2D diffuseMap;
uniform sampler2D detailMap;

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

#ifdef ATMOSPHERE_ENABLED
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform vec3 glowColor;
uniform float glowPower;
varying vec3 v_Normal;
#endif

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif

@import ecgl.common.layers.header

@import ecgl.common.uv.fragmentHeader

@import ecgl.common.wireframe.fragmentHeader

@import clay.util.srgb

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color);
#else
 gl_FragColor = color;
#endif

#ifdef VERTEX_COLOR
 gl_FragColor *= v_Color;
#endif

 @import ecgl.common.albedo.main

 @import ecgl.common.diffuseLayer.main

 gl_FragColor *= albedoTexel;

#ifdef ATMOSPHERE_ENABLED
 float atmoIntensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor.rgb += glowColor * atmoIntensity;
#endif

 @import ecgl.common.emissiveLayer.main

 @import ecgl.common.wireframe.fragmentMain

}
@end`),K.import(`/**
 * http: */

@export ecgl.lambert.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header


@import ecgl.common.attributes

@import ecgl.common.wireframe.vertexHeader

#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif


@import ecgl.common.vertexAnimation.header


varying vec3 v_Normal;
varying vec3 v_WorldPosition;

void main()
{
 @import ecgl.common.uv.main

 @import ecgl.common.vertexAnimation.main


 gl_Position = worldViewProjection * vec4(pos, 1.0);

 v_Normal = normalize((worldInverseTranspose * vec4(norm, 0.0)).xyz);
 v_WorldPosition = (world * vec4(pos, 1.0)).xyz;

#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif

 @import ecgl.common.wireframe.vertexMain
}

@end


@export ecgl.lambert.fragment

#define LAYER_DIFFUSEMAP_COUNT 0
#define LAYER_EMISSIVEMAP_COUNT 0

#define NORMAL_UP_AXIS 1
#define NORMAL_FRONT_AXIS 2

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform sampler2D diffuseMap;
uniform sampler2D detailMap;

@import ecgl.common.layers.header

uniform float emissionIntensity: 1.0;

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

uniform mat4 viewInverse : VIEWINVERSE;

#ifdef ATMOSPHERE_ENABLED
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform vec3 glowColor;
uniform float glowPower;
#endif

#ifdef AMBIENT_LIGHT_COUNT
@import clay.header.ambient_light
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
@import clay.header.ambient_sh_light
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif


@import ecgl.common.ssaoMap.header

@import ecgl.common.bumpMap.header

@import clay.util.srgb

@import ecgl.common.wireframe.fragmentHeader

@import clay.plugin.compute_shadow_map

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color);
#else
 gl_FragColor = color;
#endif

#ifdef VERTEX_COLOR
 #ifdef SRGB_DECODE
 gl_FragColor *= sRGBToLinear(v_Color);
 #else
 gl_FragColor *= v_Color;
 #endif
#endif

 @import ecgl.common.albedo.main

 @import ecgl.common.diffuseLayer.main

 gl_FragColor *= albedoTexel;

 vec3 N = v_Normal;
#ifdef DOUBLE_SIDED
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);

 if (dot(N, V) < 0.0) {
 N = -N;
 }
#endif

 float ambientFactor = 1.0;

#ifdef BUMPMAP_ENABLED
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 ambientFactor = dot(v_Normal, N);
#endif

 vec3 N2 = vec3(N.x, N[NORMAL_UP_AXIS], N[NORMAL_FRONT_AXIS]);

 vec3 diffuseColor = vec3(0.0, 0.0, 0.0);

 @import ecgl.common.ssaoMap.main

#ifdef AMBIENT_LIGHT_COUNT
 for(int i = 0; i < AMBIENT_LIGHT_COUNT; i++)
 {
 diffuseColor += ambientLightColor[i] * ambientFactor * ao;
 }
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_SH_LIGHT_COUNT; _idx_++)
 {{
 diffuseColor += calcAmbientSHLight(_idx_, N2) * ambientSHLightColor[_idx_] * ao;
 }}
#endif
#ifdef DIRECTIONAL_LIGHT_COUNT
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
#endif
 for(int i = 0; i < DIRECTIONAL_LIGHT_COUNT; i++)
 {
 vec3 lightDirection = -directionalLightDirection[i];
 vec3 lightColor = directionalLightColor[i];

 float shadowContrib = 1.0;
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 if (shadowEnabled)
 {
 shadowContrib = shadowContribsDir[i];
 }
#endif

 float ndl = dot(N, normalize(lightDirection)) * shadowContrib;

 diffuseColor += lightColor * clamp(ndl, 0.0, 1.0);
 }
#endif

 gl_FragColor.rgb *= diffuseColor;

#ifdef ATMOSPHERE_ENABLED
 float atmoIntensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor.rgb += glowColor * atmoIntensity;
#endif

 @import ecgl.common.emissiveLayer.main

 @import ecgl.common.wireframe.fragmentMain
}

@end`),K.import(`@export ecgl.realistic.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header

@import ecgl.common.attributes


@import ecgl.common.wireframe.vertexHeader

#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif

#ifdef NORMALMAP_ENABLED
attribute vec4 tangent : TANGENT;
varying vec3 v_Tangent;
varying vec3 v_Bitangent;
#endif

@import ecgl.common.vertexAnimation.header

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

void main()
{

 @import ecgl.common.uv.main

 @import ecgl.common.vertexAnimation.main

 gl_Position = worldViewProjection * vec4(pos, 1.0);

 v_Normal = normalize((worldInverseTranspose * vec4(norm, 0.0)).xyz);
 v_WorldPosition = (world * vec4(pos, 1.0)).xyz;

#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif

#ifdef NORMALMAP_ENABLED
 v_Tangent = normalize((worldInverseTranspose * vec4(tangent.xyz, 0.0)).xyz);
 v_Bitangent = normalize(cross(v_Normal, v_Tangent) * tangent.w);
#endif

 @import ecgl.common.wireframe.vertexMain

}

@end



@export ecgl.realistic.fragment

#define LAYER_DIFFUSEMAP_COUNT 0
#define LAYER_EMISSIVEMAP_COUNT 0
#define PI 3.14159265358979
#define ROUGHNESS_CHANEL 0
#define METALNESS_CHANEL 1

#define NORMAL_UP_AXIS 1
#define NORMAL_FRONT_AXIS 2

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform sampler2D diffuseMap;

uniform sampler2D detailMap;
uniform sampler2D metalnessMap;
uniform sampler2D roughnessMap;

@import ecgl.common.layers.header

uniform float emissionIntensity: 1.0;

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

uniform float metalness : 0.0;
uniform float roughness : 0.5;

uniform mat4 viewInverse : VIEWINVERSE;

#ifdef ATMOSPHERE_ENABLED
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform vec3 glowColor;
uniform float glowPower;
#endif

#ifdef AMBIENT_LIGHT_COUNT
@import clay.header.ambient_light
#endif

#ifdef AMBIENT_SH_LIGHT_COUNT
@import clay.header.ambient_sh_light
#endif

#ifdef AMBIENT_CUBEMAP_LIGHT_COUNT
@import clay.header.ambient_cubemap_light
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

@import ecgl.common.normalMap.fragmentHeader

@import ecgl.common.ssaoMap.header

@import ecgl.common.bumpMap.header

@import clay.util.srgb

@import clay.util.rgbm

@import ecgl.common.wireframe.fragmentHeader

@import clay.plugin.compute_shadow_map

vec3 F_Schlick(float ndv, vec3 spec) {
 return spec + (1.0 - spec) * pow(1.0 - ndv, 5.0);
}

float D_Phong(float g, float ndh) {
 float a = pow(8192.0, g);
 return (a + 2.0) / 8.0 * pow(ndh, a);
}

void main()
{
 vec4 albedoColor = color;

 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);
#ifdef VERTEX_COLOR
 #ifdef SRGB_DECODE
 albedoColor *= sRGBToLinear(v_Color);
 #else
 albedoColor *= v_Color;
 #endif
#endif

 @import ecgl.common.albedo.main

 @import ecgl.common.diffuseLayer.main

 albedoColor *= albedoTexel;

 float m = metalness;

#ifdef METALNESSMAP_ENABLED
 float m2 = texture2D(metalnessMap, v_DetailTexcoord)[METALNESS_CHANEL];
 m = clamp(m2 + (m - 0.5) * 2.0, 0.0, 1.0);
#endif

 vec3 baseColor = albedoColor.rgb;
 albedoColor.rgb = baseColor * (1.0 - m);
 vec3 specFactor = mix(vec3(0.04), baseColor, m);

 float g = 1.0 - roughness;

#ifdef ROUGHNESSMAP_ENABLED
 float g2 = 1.0 - texture2D(roughnessMap, v_DetailTexcoord)[ROUGHNESS_CHANEL];
 g = clamp(g2 + (g - 0.5) * 2.0, 0.0, 1.0);
#endif

 vec3 N = v_Normal;

#ifdef DOUBLE_SIDED
 if (dot(N, V) < 0.0) {
 N = -N;
 }
#endif

 float ambientFactor = 1.0;

#ifdef BUMPMAP_ENABLED
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 ambientFactor = dot(v_Normal, N);
#endif

@import ecgl.common.normalMap.fragmentMain

 vec3 N2 = vec3(N.x, N[NORMAL_UP_AXIS], N[NORMAL_FRONT_AXIS]);

 vec3 diffuseTerm = vec3(0.0);
 vec3 specularTerm = vec3(0.0);

 float ndv = clamp(dot(N, V), 0.0, 1.0);
 vec3 fresnelTerm = F_Schlick(ndv, specFactor);

 @import ecgl.common.ssaoMap.main

#ifdef AMBIENT_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_LIGHT_COUNT; _idx_++)
 {{
 diffuseTerm += ambientLightColor[_idx_] * ambientFactor * ao;
 }}
#endif

#ifdef AMBIENT_SH_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_SH_LIGHT_COUNT; _idx_++)
 {{
 diffuseTerm += calcAmbientSHLight(_idx_, N2) * ambientSHLightColor[_idx_] * ao;
 }}
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
#endif
 for(int _idx_ = 0; _idx_ < DIRECTIONAL_LIGHT_COUNT; _idx_++)
 {{
 vec3 L = -directionalLightDirection[_idx_];
 vec3 lc = directionalLightColor[_idx_];

 vec3 H = normalize(L + V);
 float ndl = clamp(dot(N, normalize(L)), 0.0, 1.0);
 float ndh = clamp(dot(N, H), 0.0, 1.0);

 float shadowContrib = 1.0;
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 if (shadowEnabled)
 {
 shadowContrib = shadowContribsDir[_idx_];
 }
#endif

 vec3 li = lc * ndl * shadowContrib;

 diffuseTerm += li;
 specularTerm += li * fresnelTerm * D_Phong(g, ndh);
 }}
#endif


#ifdef AMBIENT_CUBEMAP_LIGHT_COUNT
 vec3 L = reflect(-V, N);
 L = vec3(L.x, L[NORMAL_UP_AXIS], L[NORMAL_FRONT_AXIS]);
 float rough2 = clamp(1.0 - g, 0.0, 1.0);
 float bias2 = rough2 * 5.0;
 vec2 brdfParam2 = texture2D(ambientCubemapLightBRDFLookup[0], vec2(rough2, ndv)).xy;
 vec3 envWeight2 = specFactor * brdfParam2.x + brdfParam2.y;
 vec3 envTexel2;
 for(int _idx_ = 0; _idx_ < AMBIENT_CUBEMAP_LIGHT_COUNT; _idx_++)
 {{
 envTexel2 = RGBMDecode(textureCubeLodEXT(ambientCubemapLightCubemap[_idx_], L, bias2), 8.12);
 specularTerm += ambientCubemapLightColor[_idx_] * envTexel2 * envWeight2 * ao;
 }}
#endif

 gl_FragColor.rgb = albedoColor.rgb * diffuseTerm + specularTerm;
 gl_FragColor.a = albedoColor.a;

#ifdef ATMOSPHERE_ENABLED
 float atmoIntensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor.rgb += glowColor * atmoIntensity;
#endif

#ifdef SRGB_ENCODE
 gl_FragColor = linearTosRGB(gl_FragColor);
#endif

 @import ecgl.common.emissiveLayer.main

 @import ecgl.common.wireframe.fragmentMain
}

@end`),K.import(`@export ecgl.hatching.vertex

@import ecgl.realistic.vertex

@end


@export ecgl.hatching.fragment

#define NORMAL_UP_AXIS 1
#define NORMAL_FRONT_AXIS 2

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform vec4 color : [0.0, 0.0, 0.0, 1.0];
uniform vec4 paperColor : [1.0, 1.0, 1.0, 1.0];

uniform mat4 viewInverse : VIEWINVERSE;

#ifdef AMBIENT_LIGHT_COUNT
@import clay.header.ambient_light
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
@import clay.header.ambient_sh_light
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif


@import ecgl.common.ssaoMap.header

@import ecgl.common.bumpMap.header

@import clay.util.srgb

@import ecgl.common.wireframe.fragmentHeader

@import clay.plugin.compute_shadow_map

uniform sampler2D hatch1;
uniform sampler2D hatch2;
uniform sampler2D hatch3;
uniform sampler2D hatch4;
uniform sampler2D hatch5;
uniform sampler2D hatch6;

float shade(in float tone) {
 vec4 c = vec4(1. ,1., 1., 1.);
 float step = 1. / 6.;
 vec2 uv = v_DetailTexcoord;
 if (tone <= step / 2.0) {
 c = mix(vec4(0.), texture2D(hatch6, uv), 12. * tone);
 }
 else if (tone <= step) {
 c = mix(texture2D(hatch6, uv), texture2D(hatch5, uv), 6. * tone);
 }
 if(tone > step && tone <= 2. * step){
 c = mix(texture2D(hatch5, uv), texture2D(hatch4, uv) , 6. * (tone - step));
 }
 if(tone > 2. * step && tone <= 3. * step){
 c = mix(texture2D(hatch4, uv), texture2D(hatch3, uv), 6. * (tone - 2. * step));
 }
 if(tone > 3. * step && tone <= 4. * step){
 c = mix(texture2D(hatch3, uv), texture2D(hatch2, uv), 6. * (tone - 3. * step));
 }
 if(tone > 4. * step && tone <= 5. * step){
 c = mix(texture2D(hatch2, uv), texture2D(hatch1, uv), 6. * (tone - 4. * step));
 }
 if(tone > 5. * step){
 c = mix(texture2D(hatch1, uv), vec4(1.), 6. * (tone - 5. * step));
 }

 return c.r;
}

const vec3 w = vec3(0.2125, 0.7154, 0.0721);

void main()
{
#ifdef SRGB_DECODE
 vec4 inkColor = sRGBToLinear(color);
#else
 vec4 inkColor = color;
#endif

#ifdef VERTEX_COLOR
 #ifdef SRGB_DECODE
 inkColor *= sRGBToLinear(v_Color);
 #else
 inkColor *= v_Color;
 #endif
#endif

 vec3 N = v_Normal;
#ifdef DOUBLE_SIDED
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);

 if (dot(N, V) < 0.0) {
 N = -N;
 }
#endif

 float tone = 0.0;

 float ambientFactor = 1.0;

#ifdef BUMPMAP_ENABLED
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 ambientFactor = dot(v_Normal, N);
#endif

 vec3 N2 = vec3(N.x, N[NORMAL_UP_AXIS], N[NORMAL_FRONT_AXIS]);

 @import ecgl.common.ssaoMap.main

#ifdef AMBIENT_LIGHT_COUNT
 for(int i = 0; i < AMBIENT_LIGHT_COUNT; i++)
 {
 tone += dot(ambientLightColor[i], w) * ambientFactor * ao;
 }
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_SH_LIGHT_COUNT; _idx_++)
 {{
 tone += dot(calcAmbientSHLight(_idx_, N2) * ambientSHLightColor[_idx_], w) * ao;
 }}
#endif
#ifdef DIRECTIONAL_LIGHT_COUNT
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
#endif
 for(int i = 0; i < DIRECTIONAL_LIGHT_COUNT; i++)
 {
 vec3 lightDirection = -directionalLightDirection[i];
 float lightTone = dot(directionalLightColor[i], w);

 float shadowContrib = 1.0;
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 if (shadowEnabled)
 {
 shadowContrib = shadowContribsDir[i];
 }
#endif

 float ndl = dot(N, normalize(lightDirection)) * shadowContrib;

 tone += lightTone * clamp(ndl, 0.0, 1.0);
 }
#endif

 gl_FragColor = mix(inkColor, paperColor, shade(clamp(tone, 0.0, 1.0)));
 }
@end
`),K.import(`@export ecgl.sm.depth.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
uniform float percent : 1.0;
#endif

varying vec4 v_ViewPosition;
varying vec2 v_Texcoord;

void main(){

#ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
#else
 vec3 pos = position;
#endif

 v_ViewPosition = worldViewProjection * vec4(pos, 1.0);
 gl_Position = v_ViewPosition;

 v_Texcoord = texcoord;

}
@end



@export ecgl.sm.depth.fragment

@import clay.sm.depth.fragment

@end`);function Ki(e){return!e||e===`none`}function qi(e){return e instanceof HTMLCanvasElement||e instanceof HTMLImageElement||e instanceof Image}function Ji(e){return e.getZr&&e.setOption}var Yi=dr.prototype.addToScene,Xi=dr.prototype.removeFromScene;dr.prototype.addToScene=function(e){if(Yi.call(this,e),this.__zr){var t=this.__zr;e.traverse(function(e){e.__zr=t,e.addAnimatorsToZr&&e.addAnimatorsToZr(t)})}},dr.prototype.removeFromScene=function(e){Xi.call(this,e),e.traverse(function(e){var t=e.__zr;e.__zr=null,t&&e.removeAnimatorsFromZr&&e.removeAnimatorsFromZr(t)})},Mt.prototype.setTextureImage=function(e,t,n,r){if(this.shader){var i=n.getZr(),a=this,o;return a.autoUpdateTextureStatus=!1,a.disableTexture(e),Ki(t)||(o=Q.loadTexture(t,n,r,function(t){a.enableTexture(e),i&&i.refresh()}),a.set(e,o)),o}};var Q={};Q.Renderer=wn,Q.Node=$e,Q.Mesh=tt,Q.Shader=K,Q.Material=Mt,Q.Texture=q,Q.Texture2D=J,Q.Geometry=Y,Q.SphereGeometry=Mi,Q.PlaneGeometry=jr,Q.CubeGeometry=Nr,Q.AmbientLight=Ni,Q.DirectionalLight=Pi,Q.PointLight=Fi,Q.SpotLight=Ii,Q.PerspectiveCamera=_r,Q.OrthographicCamera=_i,Q.Vector2=G,Q.Vector3=L,Q.Vector4=Li,Q.Quaternion=We,Q.Matrix2=Bi,Q.Matrix2d=Hi,Q.Matrix3=Ui,Q.Matrix4=H,Q.Plane=Xn,Q.Ray=ir,Q.BoundingBox=Ze,Q.Frustum=nr;var Zi=null;function Qi(){return Zi===null&&(Zi=di.createBlank(`rgba(255,255,255,0)`).image),Zi}function $i(e){return 2**Math.round(Math.log(e)/Math.LN2)}function ea(e){if((e.wrapS===q.REPEAT||e.wrapT===q.REPEAT)&&e.image){var t=$i(e.width),n=$i(e.height);if(t!==e.width||n!==e.height){var r=document.createElement(`canvas`);r.width=t,r.height=n,r.getContext(`2d`).drawImage(e.image,0,0,t,n),e.image=r}}}Q.loadTexture=function(e,t,n,r){typeof n==`function`&&(r=n,n={}),n=n||{};for(var i=Object.keys(n).sort(),a=``,o=0;o<i.length;o++)a+=i[o]+`_`+n[i[o]]+`_`;var s=t.__textureCache=t.__textureCache||new ne(20);if(Ji(e)){var c=e.__textureid__,l=s.get(a+c);if(l)l.texture.surface.setECharts(e),r&&r(l.texture);else{var u=new gi(e);u.onupdate=function(){t.getZr().refresh()},l={texture:u.getTexture()};for(var o=0;o<i.length;o++)l.texture[i[o]]=n[i[o]];c=e.__textureid__||`__ecgl_ec__`+l.texture.__uid__,e.__textureid__=c,s.put(a+c,l),r&&r(l.texture)}return l.texture}else if(qi(e)){var c=e.__textureid__,l=s.get(a+c);if(!l){l={texture:new Q.Texture2D({image:e})};for(var o=0;o<i.length;o++)l.texture[i[o]]=n[i[o]];c=e.__textureid__||`__ecgl_image__`+l.texture.__uid__,e.__textureid__=c,s.put(a+c,l),ea(l.texture),r&&r(l.texture)}return l.texture}else{var l=s.get(a+e);if(l)l.callbacks?l.callbacks.push(r):r&&r(l.texture);else if(e.match(/.hdr$|^data:application\/octet-stream/)){l={callbacks:[r]};var d=di.loadTexture(e,{exposure:n.exposure,fileType:`hdr`},function(){d.dirty(),l.callbacks.forEach(function(e){e&&e(d)}),l.callbacks=null});l.texture=d,s.put(a+e,l)}else{for(var d=new Q.Texture2D({image:new Image}),o=0;o<i.length;o++)d[i[o]]=n[i[o]];l={texture:d,callbacks:[r]};var f=d.image;f.onload=function(){d.image=f,ea(d),d.dirty(),l.callbacks.forEach(function(e){e&&e(d)}),l.callbacks=null},f.crossOrigin=`Anonymous`,f.src=e,d.image=Qi(),s.put(a+e,l)}return l.texture}},Q.createAmbientCubemap=function(e,t,n,r){e=e||{};var i=e.texture,a=X.firstNotNull(e.exposure,1),o=new Ti({intensity:X.firstNotNull(e.specularIntensity,1)}),s=new Ei({intensity:X.firstNotNull(e.diffuseIntensity,1),coefficients:[.844,.712,.691,-.037,.083,.167,.343,.288,.299,-.041,-.021,-.009,-.003,-.041,-.064,-.011,-.007,-.004,-.031,.034,.081,-.06,-.049,-.06,.046,.056,.05]});return o.cubemap=Q.loadTexture(i,n,{exposure:a},function(){o.cubemap.flipY=!1,o.prefilter(t,32),s.coefficients=Di.projectEnvironmentMap(t,o.cubemap,{lod:1}),r&&r()}),{specular:o,diffuse:s}},Q.createBlankTexture=di.createBlank,Q.isImage=qi,Q.additiveBlend=function(e){e.blendEquation(e.FUNC_ADD),e.blendFunc(e.SRC_ALPHA,e.ONE)},Q.parseColor=function(e,t){return e instanceof Array?(t||(t=[]),t[0]=e[0],t[1]=e[1],t[2]=e[2],e.length>3?t[3]=e[3]:t[3]=1,t):(t=se(e||`#000`,t)||[0,0,0,0],t[0]/=255,t[1]/=255,t[2]/=255,t)},Q.directionFromAlphaBeta=function(e,t){var n=e/180*Math.PI+Math.PI/2,r=-t/180*Math.PI+Math.PI/2,i=[],a=Math.sin(n);return i[0]=a*Math.cos(r),i[1]=-Math.cos(n),i[2]=a*Math.sin(r),i},Q.getShadowResolution=function(e){var t=1024;switch(e){case`low`:t=512;break;case`medium`:break;case`high`:t=2048;break;case`ultra`:t=4096;break}return t},Q.COMMON_SHADERS=[`lambert`,`color`,`realistic`,`hatching`,`shadow`],Q.createShader=function(e){e===`ecgl.shadow`&&(e=`ecgl.displayShadow`);var t=K.source(e+`.vertex`),n=K.source(e+`.fragment`);t||console.error(`Vertex shader of '%s' not exits`,e),n||console.error(`Fragment shader of '%s' not exits`,e);var r=new K(t,n);return r.name=e,r},Q.createMaterial=function(e,t){t instanceof Array||(t=[t]);var n=new Mt({shader:Q.createShader(e)});return t.forEach(function(e){typeof e==`string`&&n.define(e)}),n},Q.setMaterialFromModel=function(e,t,n,r){t.autoUpdateTextureStatus=!1;var i=n.getModel(e+`Material`),a=i.get(`detailTexture`),o=X.firstNotNull(i.get(`textureTiling`),1),s=X.firstNotNull(i.get(`textureOffset`),0);typeof o==`number`&&(o=[o,o]),typeof s==`number`&&(s=[s,s]);var c=o[0]>1||o[1]>1?Q.Texture.REPEAT:Q.Texture.CLAMP_TO_EDGE,l={anisotropic:8,wrapS:c,wrapT:c};if(e===`realistic`){var u=i.get(`roughness`),d=i.get(`metalness`);d==null?d=0:isNaN(d)&&(t.setTextureImage(`metalnessMap`,d,r,l),d=X.firstNotNull(i.get(`metalnessAdjust`),.5)),u==null?u=.5:isNaN(u)&&(t.setTextureImage(`roughnessMap`,u,r,l),u=X.firstNotNull(i.get(`roughnessAdjust`),.5));var f=i.get(`normalTexture`);t.setTextureImage(`detailMap`,a,r,l),t.setTextureImage(`normalMap`,f,r,l),t.set({roughness:u,metalness:d,detailUvRepeat:o,detailUvOffset:s})}else if(e===`lambert`)t.setTextureImage(`detailMap`,a,r,l),t.set({detailUvRepeat:o,detailUvOffset:s});else if(e===`color`)t.setTextureImage(`detailMap`,a,r,l),t.set({detailUvRepeat:o,detailUvOffset:s});else if(e===`hatching`){var p=i.get(`hatchingTextures`)||[];p.length;for(var m=0;m<6;m++)t.setTextureImage(`hatch`+(m+1),p[m],r,{anisotropic:8,wrapS:Q.Texture.REPEAT,wrapT:Q.Texture.REPEAT});t.set({detailUvRepeat:o,detailUvOffset:s})}},Q.updateVertexAnimation=function(e,t,n,r){var i=r.get(`animation`),a=r.get(`animationDurationUpdate`),o=r.get(`animationEasingUpdate`),s=n.shadowDepthMaterial;if(i&&t&&a>0&&t.geometry.vertexCount===n.geometry.vertexCount){n.material.define(`vertex`,`VERTEX_ANIMATION`),n.ignorePreZ=!0,s&&s.define(`vertex`,`VERTEX_ANIMATION`);for(var c=0;c<e.length;c++)n.geometry.attributes[e[c][0]].value=t.geometry.attributes[e[c][1]].value;n.geometry.dirty(),n.__percent=0,n.material.set(`percent`,0),n.stopAnimation(),n.animate().when(a,{__percent:1}).during(function(){n.material.set(`percent`,n.__percent),s&&s.set(`percent`,n.__percent)}).done(function(){n.ignorePreZ=!1,n.material.undefine(`vertex`,`VERTEX_ANIMATION`),s&&s.undefine(`vertex`,`VERTEX_ANIMATION`)}).start(o)}else n.material.undefine(`vertex`,`VERTEX_ANIMATION`),s&&s.undefine(`vertex`,`VERTEX_ANIMATION`)};var ta=Fe.extend({scene:null,camera:null,renderer:null},function(){this._ray=new ir,this._ndc=new G},{pick:function(e,t,n){return this.pickAll(e,t,[],n)[0]||null},pickAll:function(e,t,n,r){return this.renderer.screenToNDC(e,t,this._ndc),this.camera.castRay(this._ndc,this._ray),n=n||[],this._intersectNode(this.scene,n,r||!1),n.sort(this._intersectionCompareFunc),n},_intersectNode:function(e,t,n){e instanceof et&&e.isRenderable()&&(!e.ignorePicking||n)&&(e.mode===U.TRIANGLES&&e.geometry.isUseIndices()||e.geometry.pickByRay||e.geometry.pick)&&this._intersectRenderable(e,t);for(var r=0;r<e._children.length;r++)this._intersectNode(e._children[r],t,n)},_intersectRenderable:(function(){var e=new L,t=new L,n=new L,r=new ir,i=new H;return function(a,o){var s=a.isSkinnedMesh();r.copy(this._ray),H.invert(i,a.worldTransform),s||r.applyTransform(i);var c=a.geometry,l=s?a.skeleton.boundingBox:c.boundingBox;if(!(l&&!r.intersectBoundingBox(l))){if(c.pick){c.pick(this._ndc.x,this._ndc.y,this.renderer,this.camera,a,o);return}else if(c.pickByRay){c.pickByRay(r,a,o);return}var u=a.cullFace===U.BACK&&a.frontFace===U.CCW||a.cullFace===U.FRONT&&a.frontFace===U.CW,d,f=c.indices,p=c.attributes.position,m=c.attributes.weight,h=c.attributes.joint,g,_=[];if(!(!p||!p.value||!f)){if(s){g=a.skeleton.getSubSkinMatrices(a.__uid__,a.joints);for(var v=0;v<a.joints.length;v++){_[v]=_[v]||[];for(var y=0;y<16;y++)_[v][y]=g[v*16+y]}var b=[],x=[],S=[],C=[],w=[],T=c.attributes.skinnedPosition;(!T||!T.value)&&(c.createAttribute(`skinnedPosition`,`f`,3),T=c.attributes.skinnedPosition,T.init(c.vertexCount));for(var v=0;v<c.vertexCount;v++){p.get(v,b),m.get(v,x),h.get(v,S),x[3]=1-x[0]-x[1]-x[2],I.set(C,0,0,0);for(var y=0;y<4;y++)S[y]>=0&&x[y]>1e-4&&(I.transformMat4(w,b,_[S[y]]),I.scaleAndAdd(C,C,w,x[y]));T.set(v,C)}}for(var v=0;v<f.length;v+=3){var E=f[v],D=f[v+1],O=f[v+2],k=s?c.attributes.skinnedPosition:p;if(k.get(E,e.array),k.get(D,t.array),k.get(O,n.array),d=u?r.intersectTriangle(e,t,n,a.culling):r.intersectTriangle(e,n,t,a.culling),d){var A=new L;s?L.copy(A,d):L.transformMat4(A,d,a.worldTransform),o.push(new ta.Intersection(d,A,a,[E,D,O],v/3,L.dist(A,this._ray.origin)))}}}}}})(),_intersectionCompareFunc:function(e,t){return e.distance-t.distance}});ta.Intersection=function(e,t,n,r,i,a){this.point=e,this.pointWorld=t,this.target=n,this.triangle=r,this.triangleIndex=i,this.distance=a};var na=function(e,t){this.id=e,this.zr=t;try{this.renderer=new wn({clearBit:0,devicePixelRatio:t.painter.dpr,preserveDrawingBuffer:!0,premultipliedAlpha:!0}),this.renderer.resize(t.painter.getWidth(),t.painter.getHeight())}catch(e){this.renderer=null,this.dom=document.createElement(`div`),this.dom.style.cssText=`position:absolute; left: 0; top: 0; right: 0; bottom: 0;`,this.dom.className=`ecgl-nowebgl`,this.dom.innerHTML=`Sorry, your browser does not support WebGL`,console.error(e);return}this.onglobalout=this.onglobalout.bind(this),t.on(`globalout`,this.onglobalout),this.dom=this.renderer.canvas;var n=this.dom.style;n.position=`absolute`,n.left=`0`,n.top=`0`,this.views=[],this._picking=new ta({renderer:this.renderer}),this._viewsToDispose=[],this._accumulatingId=0,this._zrEventProxy=new A({shape:{x:-1,y:-1,width:2,height:2},__isGLToZRProxy:!0}),this._backgroundColor=null,this._disposed=!1};na.prototype.setUnpainted=function(){},na.prototype.addView=function(e){if(e.layer!==this){var t=this._viewsToDispose.indexOf(e);t>=0&&this._viewsToDispose.splice(t,1),this.views.push(e),e.layer=this;var n=this.zr;e.scene.traverse(function(e){e.__zr=n,e.addAnimatorsToZr&&e.addAnimatorsToZr(n)})}};function ra(e){var t=e.__zr;e.__zr=null,t&&e.removeAnimatorsFromZr&&e.removeAnimatorsFromZr(t)}na.prototype.removeView=function(e){if(e.layer===this){var t=this.views.indexOf(e);t>=0&&(this.views.splice(t,1),e.scene.traverse(ra,this),e.layer=null,this._viewsToDispose.push(e))}},na.prototype.removeViewsAll=function(){this.views.forEach(function(e){e.scene.traverse(ra,this),e.layer=null,this._viewsToDispose.push(e)},this),this.views.length=0},na.prototype.resize=function(e,t){this.renderer.resize(e,t)},na.prototype.clear=function(){var e=this.renderer.gl,t=this._backgroundColor||[0,0,0,0];e.clearColor(t[0],t[1],t[2],t[3]),e.depthMask(!0),e.colorMask(!0,!0,!0,!0),e.clear(e.DEPTH_BUFFER_BIT|e.COLOR_BUFFER_BIT)},na.prototype.clearDepth=function(){var e=this.renderer.gl;e.clear(e.DEPTH_BUFFER_BIT)},na.prototype.clearColor=function(){var e=this.renderer.gl;e.clearColor(0,0,0,0),e.clear(e.COLOR_BUFFER_BIT)},na.prototype.needsRefresh=function(){this.zr.refresh()},na.prototype.refresh=function(e){this._backgroundColor=e?Q.parseColor(e):[0,0,0,0],this.renderer.clearColor=this._backgroundColor;for(var t=0;t<this.views.length;t++)this.views[t].prepareRender(this.renderer);this._doRender(!1),this._trackAndClean();for(var t=0;t<this._viewsToDispose.length;t++)this._viewsToDispose[t].dispose(this.renderer);this._viewsToDispose.length=0,this._startAccumulating()},na.prototype.renderToCanvas=function(e){this._startAccumulating(!0),e.drawImage(this.dom,0,0,e.canvas.width,e.canvas.height)},na.prototype._doRender=function(e){this.clear(),this.renderer.saveViewport();for(var t=0;t<this.views.length;t++)this.views[t].render(this.renderer,e);this.renderer.restoreViewport()},na.prototype._stopAccumulating=function(){this._accumulatingId=0,clearTimeout(this._accumulatingTimeout)};var ia=1;na.prototype._startAccumulating=function(e){var t=this;this._stopAccumulating();for(var n=!1,r=0;r<this.views.length;r++)n=this.views[r].needsAccumulate()||n;if(!n)return;function i(r){if(!(!t._accumulatingId||r!==t._accumulatingId)){for(var a=!0,o=0;o<t.views.length;o++)a=t.views[o].isAccumulateFinished()&&n;a||(t._doRender(!0),e?i(r):P(function(){i(r)}))}}this._accumulatingId=ia++,e?i(t._accumulatingId):this._accumulatingTimeout=setTimeout(function(){i(t._accumulatingId)},50)},na.prototype._trackAndClean=function(){var e=[],t=[];this._textureList&&(aa(this._textureList),aa(this._geometriesList));for(var n=0;n<this.views.length;n++)ca(this.views[n].scene,e,t);this._textureList&&(oa(this.renderer,this._textureList),oa(this.renderer,this._geometriesList)),this._textureList=e,this._geometriesList=t};function aa(e){for(var t=0;t<e.length;t++)e[t].__used__=0}function oa(e,t){for(var n=0;n<t.length;n++)t[n].__used__||t[n].dispose(e)}function sa(e,t){e.__used__=e.__used__||0,e.__used__++,e.__used__===1&&t.push(e)}function ca(e,t,n){var r,i;e.traverse(function(e){if(e.isRenderable()){var a=e.geometry,o=e.material;if(o!==r)for(var s=o.getTextureUniforms(),c=0;c<s.length;c++){var l=s[c],u=o.uniforms[l].value;if(u){if(u instanceof q)sa(u,t);else if(u instanceof Array)for(var d=0;d<u.length;d++)u[d]instanceof q&&sa(u[d],t)}}a!==i&&sa(a,n),r=o,i=a}});for(var a=0;a<e.lights.length;a++)e.lights[a].cubemap&&sa(e.lights[a].cubemap,t)}na.prototype.dispose=function(){this._disposed||(this._stopAccumulating(),this._textureList&&(aa(this._textureList),aa(this._geometriesList),oa(this.renderer,this._textureList),oa(this.renderer,this._geometriesList)),this.zr.off(`globalout`,this.onglobalout),this._disposed=!0)},na.prototype.onmousedown=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){e=e.event;var t=this.pickObject(e.offsetX,e.offsetY);t&&(this._dispatchEvent(`mousedown`,e,t),this._dispatchDataEvent(`mousedown`,e,t)),this._downX=e.offsetX,this._downY=e.offsetY}},na.prototype.onmousemove=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){e=e.event;var t=this.pickObject(e.offsetX,e.offsetY),n=t&&t.target,r=this._hovered;this._hovered=t,r&&n!==r.target&&(r.relatedTarget=n,this._dispatchEvent(`mouseout`,e,r),this.zr.setCursorStyle(`default`)),this._dispatchEvent(`mousemove`,e,t),t&&(this.zr.setCursorStyle(`pointer`),(!r||n!==r.target)&&this._dispatchEvent(`mouseover`,e,t)),this._dispatchDataEvent(`mousemove`,e,t)}},na.prototype.onmouseup=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){e=e.event;var t=this.pickObject(e.offsetX,e.offsetY);t&&(this._dispatchEvent(`mouseup`,e,t),this._dispatchDataEvent(`mouseup`,e,t)),this._upX=e.offsetX,this._upY=e.offsetY}},na.prototype.onclick=na.prototype.dblclick=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){var t=this._upX-this._downX,n=this._upY-this._downY;if(!(Math.sqrt(t*t+n*n)>20)){e=e.event;var r=this.pickObject(e.offsetX,e.offsetY);r&&(this._dispatchEvent(e.type,e,r),this._dispatchDataEvent(e.type,e,r));var i=this._clickToSetFocusPoint(e);i&&i.view.setDOFFocusOnPoint(i.distance)&&this.zr.refresh()}}},na.prototype._clickToSetFocusPoint=function(e){for(var t=this.renderer,n=t.viewport,r=this.views.length-1;r>=0;r--){var i=this.views[r];if(i.hasDOF()&&i.containPoint(e.offsetX,e.offsetY)){this._picking.scene=i.scene,this._picking.camera=i.camera,t.viewport=i.viewport;var a=this._picking.pick(e.offsetX,e.offsetY,!0);if(a)return a.view=i,a}}t.viewport=n},na.prototype.onglobalout=function(e){var t=this._hovered;t&&this._dispatchEvent(`mouseout`,e,{target:t.target})},na.prototype.pickObject=function(e,t){for(var n=[],r=this.renderer,i=r.viewport,a=0;a<this.views.length;a++){var o=this.views[a];o.containPoint(e,t)&&(this._picking.scene=o.scene,this._picking.camera=o.camera,r.viewport=o.viewport,this._picking.pickAll(e,t,n))}return r.viewport=i,n.sort(function(e,t){return e.distance-t.distance}),n[0]},na.prototype._dispatchEvent=function(e,t,n){n||(n={});var r=n.target;for(n.cancelBubble=!1,n.event=t,n.type=e,n.offsetX=t.offsetX,n.offsetY=t.offsetY;r&&(r.trigger(e,n),r=r.getParent(),!n.cancelBubble););this._dispatchToView(e,n)},na.prototype._dispatchDataEvent=function(e,t,n){var r=n&&n.target,i=r&&r.dataIndex,a=r&&r.seriesIndex,o=r&&r.eventData,s=!1,c=this._zrEventProxy;c.x=t.offsetX,c.y=t.offsetY,c.update();var l={target:c};let u=me(c);e===`mousemove`&&(i==null?o!=null&&o!==this._lastEventData&&(this._lastEventData!=null&&(u.eventData=this._lastEventData,this.zr.handler.dispatchToElement(l,`mouseout`,t)),s=!0):i!==this._lastDataIndex&&(parseInt(this._lastDataIndex,10)>=0&&(u.dataIndex=this._lastDataIndex,u.seriesIndex=this._lastSeriesIndex,this.zr.handler.dispatchToElement(l,`mouseout`,t)),s=!0),this._lastEventData=o,this._lastDataIndex=i,this._lastSeriesIndex=a),u.eventData=o,u.dataIndex=i,u.seriesIndex=a,(o!=null||parseInt(i,10)>=0&&parseInt(a,10)>=0)&&(this.zr.handler.dispatchToElement(l,e,t),s&&this.zr.handler.dispatchToElement(l,`mouseover`,t))},na.prototype._dispatchToView=function(e,t){for(var n=0;n<this.views.length;n++)this.views[n].containPoint(t.offsetX,t.offsetY)&&this.views[n].trigger(e,t)},Object.assign(na.prototype,je);var la=[`bar3D`,`line3D`,`map3D`,`scatter3D`,`surface`,`lines3D`,`scatterGL`,`scatter3D`];function ua(e,t){if(e&&e[t]&&(e[t].normal||e[t].emphasis)){var n=e[t].normal,r=e[t].emphasis;n&&(e[t]=n),r&&(e.emphasis=e.emphasis||{},e.emphasis[t]=r)}}function da(e){ua(e,`itemStyle`),ua(e,`lineStyle`),ua(e,`areaStyle`),ua(e,`label`)}function fa(e){e&&(e instanceof Array||(e=[e]),a(e,function(e){if(e.axisLabel){var t=e.axisLabel;Object.assign(t,t.textStyle),t.textStyle=null}}))}function pa(e){a(e.series,function(t){i(la,t.type)>=0&&(da(t),t.coordinateSystem===`mapbox`&&(t.coordinateSystem=`mapbox3D`,e.mapbox3D=e.mapbox))}),fa(e.xAxis3D),fa(e.yAxis3D),fa(e.zAxis3D),fa(e.grid3D),ua(e.geo3D)}function ma(e,t,n){try{return Object.defineProperty(e,t,{value:n,configurable:!0,writable:!0}),!0}catch(e){}try{return Reflect.set(e,t,n)}catch(e){}return!1}var ha=pe;ma(ha,`graphicGL`,Q);function ga(e){this._layers={},this._zr=e}ga.prototype.update=function(e,t){var n=this,r=t.getZr();if(!r.getWidth()||!r.getHeight()){console.warn(`Dom has no width or height`);return}function i(e){r.setSleepAfterStill(0);var t=(e.coordinateSystem&&e.coordinateSystem.model,e.get(`zlevel`)),i=n._layers,a=i[t];if(!a){if(a=i[t]=new na(`gl-`+t,r),r.painter.isSingleCanvas()){a.virtual=!0;var o=new ha.graphic.Image({z:1e4,style:{image:a.renderer.canvas},silent:!0});a.__hostImage=o,r.add(o)}r.painter.insertLayer(t,a)}return a.__hostImage&&a.__hostImage.setStyle({width:a.renderer.getWidth(),height:a.renderer.getHeight()}),a}function a(e,t){e&&e.traverse(function(e){e.isRenderable&&e.isRenderable()&&(e.ignorePicking=e.$ignorePicking==null?t:e.$ignorePicking)})}for(var o in this._layers)this._layers[o].removeViewsAll();e.eachComponent(function(n,r){if(n!==`series`){var o=t.getViewOfComponentModel(r),s=r.coordinateSystem;if(o.__ecgl__){var c;if(s){if(!s.viewGL){console.error(`Can't find viewGL in coordinateSystem of component `+r.id);return}c=s.viewGL}else{if(!r.viewGL){console.error(`Can't find viewGL of component `+r.id);return}c=s.viewGL}var c=s.viewGL,l=i(r);l.addView(c),o.afterRender&&o.afterRender(r,e,t,l),a(o.groupGL,r.get(`silent`))}}}),e.eachSeries(function(n){var r=t.getViewOfSeriesModel(n),o=n.coordinateSystem;if(r.__ecgl__){if(o&&!o.viewGL&&!r.viewGL){console.error(`Can't find viewGL of series `+r.id);return}var s=o&&o.viewGL||r.viewGL,c=i(n);c.addView(s),r.afterRender&&r.afterRender(n,e,t,c),a(r.groupGL,n.get(`silent`))}})},ha.registerPostInit(function(e){var t=e.getZr(),n=t.painter.dispose;t.painter.dispose=function(){typeof this.eachOtherLayer==`function`&&this.eachOtherLayer(function(e){e instanceof na&&e.dispose()}),n.call(this)}}),ha.registerPostUpdate(function(e,t){var n=t.getZr();(n.__egl=n.__egl||new ga(n)).update(e,t)}),ha.registerPreprocessor(pa);var _a={defaultOption:{viewControl:{projection:`perspective`,autoRotate:!1,autoRotateDirection:`cw`,autoRotateSpeed:10,autoRotateAfterStill:3,damping:.8,rotateSensitivity:1,zoomSensitivity:1,panSensitivity:1,panMouseButton:`middle`,rotateMouseButton:`left`,distance:150,minDistance:40,maxDistance:400,orthographicSize:150,maxOrthographicSize:400,minOrthographicSize:20,center:[0,0,0],alpha:0,beta:0,minAlpha:-90,maxAlpha:90}},setView:function(e){e=e||{},this.option.viewControl=this.option.viewControl||{},e.alpha!=null&&(this.option.viewControl.alpha=e.alpha),e.beta!=null&&(this.option.viewControl.beta=e.beta),e.distance!=null&&(this.option.viewControl.distance=e.distance),e.center!=null&&(this.option.viewControl.center=e.center)}},va={defaultOption:{postEffect:{enable:!1,bloom:{enable:!0,intensity:.1},depthOfField:{enable:!1,focalRange:20,focalDistance:50,blurRadius:10,fstop:2.8,quality:`medium`},screenSpaceAmbientOcclusion:{enable:!1,radius:2,quality:`medium`,intensity:1},screenSpaceReflection:{enable:!1,quality:`medium`,maxRoughness:.8},colorCorrection:{enable:!0,exposure:0,brightness:0,contrast:1,saturation:1,lookupTexture:``},edge:{enable:!1},FXAA:{enable:!1}},temporalSuperSampling:{enable:`auto`}}},ya={defaultOption:{light:{main:{shadow:!1,shadowQuality:`high`,color:`#fff`,intensity:1,alpha:0,beta:0},ambient:{color:`#fff`,intensity:.2},ambientCubemap:{texture:null,exposure:1,diffuseIntensity:.5,specularIntensity:.5}}}},ba=D.extend({type:`grid3D`,dependencies:[`xAxis3D`,`yAxis3D`,`zAxis3D`],defaultOption:{show:!0,zlevel:-10,left:0,top:0,width:`100%`,height:`100%`,environment:`auto`,boxWidth:100,boxHeight:100,boxDepth:100,axisPointer:{show:!0,lineStyle:{color:`rgba(0, 0, 0, 0.8)`,width:1},label:{show:!0,formatter:null,margin:8,textStyle:{fontSize:14,color:`#fff`,backgroundColor:`rgba(0,0,0,0.5)`,padding:3,borderRadius:3}}},axisLine:{show:!0,lineStyle:{color:`#333`,width:2,type:`solid`}},axisTick:{show:!0,inside:!1,length:3,lineStyle:{width:1}},axisLabel:{show:!0,inside:!1,rotate:0,margin:8,textStyle:{fontSize:12}},splitLine:{show:!0,lineStyle:{color:[`#ccc`],width:1,type:`solid`}},splitArea:{show:!1,areaStyle:{color:[`rgba(250,250,250,0.3)`,`rgba(200,200,200,0.3)`]}},light:{main:{alpha:30,beta:40},ambient:{intensity:.4}},viewControl:{alpha:20,beta:40,autoRotate:!1,distance:200,minDistance:40,maxDistance:400}}});m(ba.prototype,_a),m(ba.prototype,va),m(ba.prototype,ya);var xa=X.firstNotNull,Sa={left:0,middle:1,right:2};function Ca(e){return e instanceof Array||(e=[e,e]),e}var wa=Fe.extend(function(){return{zr:null,viewGL:null,_center:new L,minDistance:.5,maxDistance:1.5,maxOrthographicSize:300,minOrthographicSize:30,minAlpha:-90,maxAlpha:90,minBeta:-1/0,maxBeta:1/0,autoRotateAfterStill:0,autoRotateDirection:`cw`,autoRotateSpeed:60,damping:.8,rotateSensitivity:1,zoomSensitivity:1,panSensitivity:1,panMouseButton:`middle`,rotateMouseButton:`left`,_mode:`rotate`,_camera:null,_needsUpdate:!1,_rotating:!1,_phi:0,_theta:0,_mouseX:0,_mouseY:0,_rotateVelocity:new G,_panVelocity:new G,_distance:500,_zoomSpeed:0,_stillTimeout:0,_animators:[]}},function(){[`_mouseDownHandler`,`_mouseWheelHandler`,`_mouseMoveHandler`,`_mouseUpHandler`,`_pinchHandler`,`_contextMenuHandler`,`_update`].forEach(function(e){this[e]=this[e].bind(this)},this)},{init:function(){var e=this.zr;e&&(e.on(`mousedown`,this._mouseDownHandler),e.on(`globalout`,this._mouseUpHandler),e.on(`mousewheel`,this._mouseWheelHandler),e.on(`pinch`,this._pinchHandler),e.animation.on(`frame`,this._update),e.dom.addEventListener(`contextmenu`,this._contextMenuHandler))},dispose:function(){var e=this.zr;e&&(e.off(`mousedown`,this._mouseDownHandler),e.off(`mousemove`,this._mouseMoveHandler),e.off(`mouseup`,this._mouseUpHandler),e.off(`mousewheel`,this._mouseWheelHandler),e.off(`pinch`,this._pinchHandler),e.off(`globalout`,this._mouseUpHandler),e.dom.removeEventListener(`contextmenu`,this._contextMenuHandler),e.animation.off(`frame`,this._update)),this.stopAllAnimation()},getDistance:function(){return this._distance},setDistance:function(e){this._distance=e,this._needsUpdate=!0},getOrthographicSize:function(){return this._orthoSize},setOrthographicSize:function(e){this._orthoSize=e,this._needsUpdate=!0},getAlpha:function(){return this._theta/Math.PI*180},getBeta:function(){return-this._phi/Math.PI*180},getCenter:function(){return this._center.toArray()},setAlpha:function(e){e=Math.max(Math.min(this.maxAlpha,e),this.minAlpha),this._theta=e/180*Math.PI,this._needsUpdate=!0},setBeta:function(e){e=Math.max(Math.min(this.maxBeta,e),this.minBeta),this._phi=-e/180*Math.PI,this._needsUpdate=!0},setCenter:function(e){this._center.setArray(e)},setViewGL:function(e){this.viewGL=e},getCamera:function(){return this.viewGL.camera},setFromViewControlModel:function(e,t){t=t||{};var n=t.baseDistance||0,r=t.baseOrthoSize||1,i=e.get(`projection`);i!==`perspective`&&i!==`orthographic`&&i!==`isometric`&&(i=`perspective`),this._projection=i,this.viewGL.setProjection(i);var a=e.get(`distance`)+n,o=e.get(`orthographicSize`)+r;[[`damping`,.8],[`autoRotate`,!1],[`autoRotateAfterStill`,3],[`autoRotateDirection`,`cw`],[`autoRotateSpeed`,10],[`minDistance`,30],[`maxDistance`,400],[`minOrthographicSize`,30],[`maxOrthographicSize`,300],[`minAlpha`,-90],[`maxAlpha`,90],[`minBeta`,-1/0],[`maxBeta`,1/0],[`rotateSensitivity`,1],[`zoomSensitivity`,1],[`panSensitivity`,1],[`panMouseButton`,`left`],[`rotateMouseButton`,`middle`]].forEach(function(t){this[t[0]]=xa(e.get(t[0]),t[1])},this),this.minDistance+=n,this.maxDistance+=n,this.minOrthographicSize+=r,this.maxOrthographicSize+=r;var s=e.ecModel,c={};[`animation`,`animationDurationUpdate`,`animationEasingUpdate`].forEach(function(t){c[t]=xa(e.get(t),s&&s.get(t))});var l=xa(t.alpha,e.get(`alpha`))||0,u=xa(t.beta,e.get(`beta`))||0,d=xa(t.center,e.get(`center`))||[0,0,0];c.animation&&c.animationDurationUpdate>0&&this._notFirst?this.animateTo({alpha:l,beta:u,center:d,distance:a,orthographicSize:o,easing:c.animationEasingUpdate,duration:c.animationDurationUpdate}):(this.setDistance(a),this.setAlpha(l),this.setBeta(u),this.setCenter(d),this.setOrthographicSize(o)),this._notFirst=!0,this._validateProperties()},_validateProperties:function(){},animateTo:function(e){var t=this.zr,n=this,r={},i={};return e.distance!=null&&(r.distance=this.getDistance(),i.distance=e.distance),e.orthographicSize!=null&&(r.orthographicSize=this.getOrthographicSize(),i.orthographicSize=e.orthographicSize),e.alpha!=null&&(r.alpha=this.getAlpha(),i.alpha=e.alpha),e.beta!=null&&(r.beta=this.getBeta(),i.beta=e.beta),e.center!=null&&(r.center=this.getCenter(),i.center=e.center),this._addAnimator(t.animation.animate(r).when(e.duration||1e3,i).during(function(){r.alpha!=null&&n.setAlpha(r.alpha),r.beta!=null&&n.setBeta(r.beta),r.distance!=null&&n.setDistance(r.distance),r.center!=null&&n.setCenter(r.center),r.orthographicSize!=null&&n.setOrthographicSize(r.orthographicSize),n._needsUpdate=!0})).start(e.easing||`linear`)},stopAllAnimation:function(){for(var e=0;e<this._animators.length;e++)this._animators[e].stop();this._animators.length=0},update:function(){this._needsUpdate=!0,this._update(20)},_isAnimating:function(){return this._animators.length>0},_update:function(e){if(this._rotating){var t=(this.autoRotateDirection===`cw`?1:-1)*this.autoRotateSpeed/180*Math.PI;this._phi-=t*e/1e3,this._needsUpdate=!0}else this._rotateVelocity.len()>0&&(this._needsUpdate=!0);(Math.abs(this._zoomSpeed)>.1||this._panVelocity.len()>0)&&(this._needsUpdate=!0),this._needsUpdate&&(e=Math.min(e,50),this._updateDistanceOrSize(e),this._updatePan(e),this._updateRotate(e),this._updateTransform(),this.getCamera().update(),this.zr&&this.zr.refresh(),this.trigger(`update`),this._needsUpdate=!1)},_updateRotate:function(e){var t=this._rotateVelocity;this._phi=t.y*e/20+this._phi,this._theta=t.x*e/20+this._theta,this.setAlpha(this.getAlpha()),this.setBeta(this.getBeta()),this._vectorDamping(t,this.damping**(e/16))},_updateDistanceOrSize:function(e){this._projection===`perspective`?this._setDistance(this._distance+this._zoomSpeed*e/20):this._setOrthoSize(this._orthoSize+this._zoomSpeed*e/20),this._zoomSpeed*=this.damping**(e/16)},_setDistance:function(e){this._distance=Math.max(Math.min(e,this.maxDistance),this.minDistance)},_setOrthoSize:function(e){this._orthoSize=Math.max(Math.min(e,this.maxOrthographicSize),this.minOrthographicSize);var t=this.getCamera(),n=this._orthoSize,r=n/this.viewGL.viewport.height*this.viewGL.viewport.width;t.left=-r/2,t.right=r/2,t.top=n/2,t.bottom=-n/2},_updatePan:function(e){var t=this._panVelocity,n=this._distance,r=this.getCamera(),i=r.worldTransform.y,a=r.worldTransform.x;this._center.scaleAndAdd(a,-t.x*n/200).scaleAndAdd(i,-t.y*n/200),this._vectorDamping(t,0)},_updateTransform:function(){var e=this.getCamera(),t=new L,n=this._theta+Math.PI/2,r=this._phi+Math.PI/2,i=Math.sin(n);t.x=i*Math.cos(r),t.y=-Math.cos(n),t.z=i*Math.sin(r),e.position.copy(this._center).scaleAndAdd(t,this._distance),e.rotation.identity().rotateY(-this._phi).rotateX(-this._theta)},_startCountingStill:function(){clearTimeout(this._stillTimeout);var e=this.autoRotateAfterStill,t=this;!isNaN(e)&&e>0&&(this._stillTimeout=setTimeout(function(){t._rotating=!0},e*1e3))},_vectorDamping:function(e,t){var n=e.len();n*=t,n<1e-4&&(n=0),e.normalize().scale(n)},_decomposeTransform:function(){if(this.getCamera()){this.getCamera().updateWorldTransform();var e=this.getCamera().worldTransform.z,t=Math.asin(e.y),n=Math.atan2(e.x,e.z);this._theta=t,this._phi=-n,this.setBeta(this.getBeta()),this.setAlpha(this.getAlpha()),this.getCamera().aspect?this._setDistance(this.getCamera().position.dist(this._center)):this._setOrthoSize(this.getCamera().top-this.getCamera().bottom)}},_mouseDownHandler:function(e){if(!e.target&&!this._isAnimating()){var t=e.offsetX,n=e.offsetY;this.viewGL&&!this.viewGL.containPoint(t,n)||(this.zr.on(`mousemove`,this._mouseMoveHandler),this.zr.on(`mouseup`,this._mouseUpHandler),e.event.targetTouches?e.event.targetTouches.length===1&&(this._mode=`rotate`):e.event.button===Sa[this.rotateMouseButton]?this._mode=`rotate`:e.event.button===Sa[this.panMouseButton]?this._mode=`pan`:this._mode=``,this._rotateVelocity.set(0,0),this._rotating=!1,this.autoRotate&&this._startCountingStill(),this._mouseX=e.offsetX,this._mouseY=e.offsetY)}},_mouseMoveHandler:function(e){if(!(e.target&&e.target.__isGLToZRProxy)&&!this._isAnimating()){var t=Ca(this.panSensitivity),n=Ca(this.rotateSensitivity);this._mode===`rotate`?(this._rotateVelocity.y=(e.offsetX-this._mouseX)/this.zr.getHeight()*2*n[0],this._rotateVelocity.x=(e.offsetY-this._mouseY)/this.zr.getWidth()*2*n[1]):this._mode===`pan`&&(this._panVelocity.x=(e.offsetX-this._mouseX)/this.zr.getWidth()*t[0]*400,this._panVelocity.y=(-e.offsetY+this._mouseY)/this.zr.getHeight()*t[1]*400),this._mouseX=e.offsetX,this._mouseY=e.offsetY,e.event.preventDefault()}},_mouseWheelHandler:function(e){if(!this._isAnimating()){var t=e.event.wheelDelta||-e.event.detail;this._zoomHandler(e,t)}},_pinchHandler:function(e){this._isAnimating()||(this._zoomHandler(e,e.pinchScale>1?1:-1),this._mode=``)},_zoomHandler:function(e,t){if(t!==0){var n=e.offsetX,r=e.offsetY;if(!(this.viewGL&&!this.viewGL.containPoint(n,r))){var i=this._projection===`perspective`?Math.max(Math.max(Math.min(this._distance-this.minDistance,this.maxDistance-this._distance))/20,.5):Math.max(Math.max(Math.min(this._orthoSize-this.minOrthographicSize,this.maxOrthographicSize-this._orthoSize))/20,.5);this._zoomSpeed=(t>0?-1:1)*i*this.zoomSensitivity,this._rotating=!1,this.autoRotate&&this._mode===`rotate`&&this._startCountingStill(),e.event.preventDefault()}}},_mouseUpHandler:function(){this.zr.off(`mousemove`,this._mouseMoveHandler),this.zr.off(`mouseup`,this._mouseUpHandler)},_isRightMouseButtonUsed:function(){return this.rotateMouseButton===`right`||this.panMouseButton===`right`},_contextMenuHandler:function(e){this._isRightMouseButtonUsed()&&e.preventDefault()},_addAnimator:function(e){var t=this._animators;return t.push(e),e.done(function(){var n=t.indexOf(e);n>=0&&t.splice(n,1)}),e}});Object.defineProperty(wa.prototype,"autoRotate",{get:function(e){return this._autoRotate},set:function(e){this._autoRotate=e,this._rotating=e}});var Ta={convertToDynamicArray:function(e){e&&this.resetOffset();var t=this.attributes;for(var n in t)e||!t[n].value?t[n].value=[]:t[n].value=Array.prototype.slice.call(t[n].value);e||!this.indices?this.indices=[]:this.indices=Array.prototype.slice.call(this.indices)},convertToTypedArray:function(){var e=this.attributes;for(var t in e)e[t].value&&e[t].value.length>0?e[t].value=new Float32Array(e[t].value):e[t].value=null;this.indices&&this.indices.length>0&&(this.indices=this.vertexCount>65535?new Uint32Array(this.indices):new Uint16Array(this.indices)),this.dirty()}},Ea={vec2:W,vec3:I,vec4:R,mat2:Z,mat2d:Vi,mat3:z,mat4:V,quat:B},Da=Ea.vec3,Oa=[[0,0],[1,1]],ka=Y.extend(function(){return{segmentScale:1,dynamic:!0,useNativeLine:!0,attributes:{position:new Y.Attribute(`position`,`float`,3,`POSITION`),positionPrev:new Y.Attribute(`positionPrev`,`float`,3),positionNext:new Y.Attribute(`positionNext`,`float`,3),prevPositionPrev:new Y.Attribute(`prevPositionPrev`,`float`,3),prevPosition:new Y.Attribute(`prevPosition`,`float`,3),prevPositionNext:new Y.Attribute(`prevPositionNext`,`float`,3),offset:new Y.Attribute(`offset`,`float`,1),color:new Y.Attribute(`color`,`float`,4,`COLOR`)}}},{resetOffset:function(){this._vertexOffset=0,this._triangleOffset=0,this._itemVertexOffsets=[]},setVertexCount:function(e){var t=this.attributes;this.vertexCount!==e&&(t.position.init(e),t.color.init(e),this.useNativeLine||(t.positionPrev.init(e),t.positionNext.init(e),t.offset.init(e)),e>65535?this.indices instanceof Uint16Array&&(this.indices=new Uint32Array(this.indices)):this.indices instanceof Uint32Array&&(this.indices=new Uint16Array(this.indices)))},setTriangleCount:function(e){this.triangleCount!==e&&(e===0?this.indices=null:this.indices=this.vertexCount>65535?new Uint32Array(e*3):new Uint16Array(e*3))},_getCubicCurveApproxStep:function(e,t,n,r){return 1/(Da.dist(e,t)+Da.dist(n,t)+Da.dist(r,n)+1)*this.segmentScale},getCubicCurveVertexCount:function(e,t,n,r){var i=this._getCubicCurveApproxStep(e,t,n,r),a=Math.ceil(1/i);return this.useNativeLine?a*2:a*2+2},getCubicCurveTriangleCount:function(e,t,n,r){var i=this._getCubicCurveApproxStep(e,t,n,r),a=Math.ceil(1/i);return this.useNativeLine?0:a*2},getLineVertexCount:function(){return this.getPolylineVertexCount(Oa)},getLineTriangleCount:function(){return this.getPolylineTriangleCount(Oa)},getPolylineVertexCount:function(e){var t=typeof e==`number`?e:typeof e[0]==`number`?e.length/3:e.length;return this.useNativeLine?(t-1)*2:(t-1)*2+2},getPolylineTriangleCount:function(e){var t=typeof e==`number`?e:typeof e[0]==`number`?e.length/3:e.length;return this.useNativeLine?0:Math.max(t-1,0)*2},addCubicCurve:function(e,t,n,r,i,a){a==null&&(a=1);for(var o=e[0],s=e[1],c=e[2],l=t[0],u=t[1],d=t[2],f=n[0],p=n[1],m=n[2],h=r[0],g=r[1],_=r[2],v=this._getCubicCurveApproxStep(e,t,n,r),y=v*v,b=y*v,x=3*v,S=3*y,C=6*y,w=6*b,T=o-l*2+f,E=s-u*2+p,D=c-d*2+m,O=(l-f)*3-o+h,k=(u-p)*3-s+g,A=(d-m)*3-c+_,j=o,M=s,N=c,ee=(l-o)*x+T*S+O*b,te=(u-s)*x+E*S+k*b,P=(d-c)*x+D*S+A*b,ne=T*C+O*w,re=E*C+k*w,ie=D*C+A*w,ae=O*w,F=k*w,oe=A*w,se=0,ce=0,le=Math.ceil(1/v),ue=new Float32Array((le+1)*3),ue=[],de=0,ce=0;ce<le+1;ce++)ue[de++]=j,ue[de++]=M,ue[de++]=N,j+=ee,M+=te,N+=P,ee+=ne,te+=re,P+=ie,ne+=ae,re+=F,ie+=oe,se+=v,se>1&&(j=ee>0?Math.min(j,h):Math.max(j,h),M=te>0?Math.min(M,g):Math.max(M,g),N=P>0?Math.min(N,_):Math.max(N,_));return this.addPolyline(ue,i,a)},addLine:function(e,t,n,r){return this.addPolyline([e,t],n,r)},addPolyline:function(e,t,n,r,i){if(e.length){var a=typeof e[0]!=`number`;if(i==null&&(i=a?e.length:e.length/3),!(i<2)){r==null&&(r=0),n==null&&(n=1),this._itemVertexOffsets.push(this._vertexOffset);var a=typeof e[0]!=`number`,o=a?typeof t[0]!=`number`:t.length/4===i,s=this.attributes.position,c=this.attributes.positionPrev,l=this.attributes.positionNext,u=this.attributes.color,d=this.attributes.offset,f=this.indices,p=this._vertexOffset,m,h;n=Math.max(n,.01);for(var g=r;g<i;g++){if(a)m=e[g],h=o?t[g]:t;else{var _=g*3;if(m=m||[],m[0]=e[_],m[1]=e[_+1],m[2]=e[_+2],o){var v=g*4;h=h||[],h[0]=t[v],h[1]=t[v+1],h[2]=t[v+2],h[3]=t[v+3]}else h=t}if(this.useNativeLine?g>1&&(s.copy(p,p-1),u.copy(p,p-1),p++):(g<i-1&&(c.set(p+2,m),c.set(p+3,m)),g>0&&(l.set(p-2,m),l.set(p-1,m)),s.set(p,m),s.set(p+1,m),u.set(p,h),u.set(p+1,h),d.set(p,n/2),d.set(p+1,-n/2),p+=2),this.useNativeLine)u.set(p,h),s.set(p,m),p++;else if(g>0){var y=this._triangleOffset*3,f=this.indices;f[y]=p-4,f[y+1]=p-3,f[y+2]=p-2,f[y+3]=p-3,f[y+4]=p-1,f[y+5]=p-2,this._triangleOffset+=2}}if(!this.useNativeLine){var b=this._vertexOffset,x=this._vertexOffset+i*2;c.copy(b,b+2),c.copy(b+1,b+3),l.copy(x-1,x-3),l.copy(x-2,x-4)}return this._vertexOffset=p,this._vertexOffset}}},setItemColor:function(e,t){for(var n=this._itemVertexOffsets[e],r=e<this._itemVertexOffsets.length-1?this._itemVertexOffsets[e+1]:this._vertexOffset,i=n;i<r;i++)this.attributes.color.set(i,t);this.dirty(`color`)},currentTriangleOffset:function(){return this._triangleOffset},currentVertexOffset:function(){return this._vertexOffset}});C(ka.prototype,Ta);function Aa(e,t,n,r,i,a,o){this._zr=e,this._x=0,this._y=0,this._rowHeight=0,this.width=r,this.height=i,this.offsetX=t,this.offsetY=n,this.dpr=o,this.gap=a}Aa.prototype={constructor:Aa,clear:function(){this._x=0,this._y=0,this._rowHeight=0},add:function(e,t,n){var r=e.getBoundingRect();t==null&&(t=r.width),n==null&&(n=r.height),t*=this.dpr,n*=this.dpr,this._fitElement(e,t,n);var i=this._x,a=this._y,o=this.width*this.dpr,s=this.height*this.dpr,c=this.gap;if(i+t+c>o&&(i=this._x=0,a+=this._rowHeight+c,this._y=a,this._rowHeight=0),this._x+=t+c,this._rowHeight=Math.max(this._rowHeight,n),a+n+c>s)return null;e.x+=this.offsetX*this.dpr+i,e.y+=this.offsetY*this.dpr+a,this._zr.add(e);var l=[this.offsetX/this.width,this.offsetY/this.height];return[[i/o+l[0],a/s+l[1]],[(i+t)/o+l[0],(a+n)/s+l[1]]]},_fitElement:function(e,t,n){var r=e.getBoundingRect(),i=t/r.width,a=n/r.height;e.x=-r.x*i,e.y=-r.y*a,e.scaleX=i,e.scaleY=a,e.update()}};function ja(e){e=e||{},e.width=e.width||512,e.height=e.height||512,e.devicePixelRatio=e.devicePixelRatio||1,e.gap=e.gap==null?2:e.gap;var t=document.createElement(`canvas`);t.width=e.width*e.devicePixelRatio,t.height=e.height*e.devicePixelRatio,this._canvas=t,this._texture=new J({image:t,flipY:!1});var n=this;this._zr=N(t),pi(this._zr,function(){n._texture.dirty(),n.onupdate&&n.onupdate()}),this._dpr=e.devicePixelRatio,this._coords={},this.onupdate=e.onupdate,this._gap=e.gap,this._textureAtlasNodes=[new Aa(this._zr,0,0,e.width,e.height,this._gap,this._dpr)],this._nodeWidth=e.width,this._nodeHeight=e.height,this._currentNodeIdx=0}ja.prototype={clear:function(){for(var e=0;e<this._textureAtlasNodes.length;e++)this._textureAtlasNodes[e].clear();this._currentNodeIdx=0,this._zr.clear(),this._coords={}},getWidth:function(){return this._width},getHeight:function(){return this._height},getTexture:function(){return this._texture},getDevicePixelRatio:function(){return this._dpr},getZr:function(){return this._zr},_getCurrentNode:function(){return this._textureAtlasNodes[this._currentNodeIdx]},_expand:function(){if(this._currentNodeIdx++,this._textureAtlasNodes[this._currentNodeIdx])return this._textureAtlasNodes[this._currentNodeIdx];var e=4096/this._dpr,t=this._textureAtlasNodes.length,n=t*this._nodeWidth%e,r=Math.floor(t*this._nodeWidth/e)*this._nodeHeight;if(!(r>=e)){var i=(n+this._nodeWidth)*this._dpr,a=(r+this._nodeHeight)*this._dpr;try{this._zr.resize({width:i,height:a})}catch(e){this._canvas.width=i,this._canvas.height=a}var o=new Aa(this._zr,n,r,this._nodeWidth,this._nodeHeight,this._gap,this._dpr);return this._textureAtlasNodes.push(o),o}},add:function(e,t,n){if(this._coords[e.id])return this._coords[e.id];var r=this._getCurrentNode().add(e,t,n);if(!r){var i=this._expand();if(!i)return;r=i.add(e,t,n)}return this._coords[e.id]=r,r},getCoordsScale:function(){var e=this._dpr;return[this._nodeWidth/this._canvas.width*e,this._nodeHeight/this._canvas.height*e]},getCoords:function(e){return this._coords[e]},dispose:function(){this._zr.dispose()}};function Ma(){}Ma.prototype={constructor:Ma,setScene:function(e){this._scene=e,this._skybox&&this._skybox.attachScene(this._scene)},initLight:function(e){this._lightRoot=e,this.mainLight=new Q.DirectionalLight({shadowBias:.005}),this.ambientLight=new Q.AmbientLight,e.add(this.mainLight),e.add(this.ambientLight)},dispose:function(){this._lightRoot&&(this._lightRoot.remove(this.mainLight),this._lightRoot.remove(this.ambientLight))},updateLight:function(e){var t=this.mainLight,n=this.ambientLight,r=e.getModel(`light`),i=r.getModel(`main`),a=r.getModel(`ambient`);t.intensity=i.get(`intensity`),n.intensity=a.get(`intensity`),t.color=Q.parseColor(i.get(`color`)).slice(0,3),n.color=Q.parseColor(a.get(`color`)).slice(0,3);var o=i.get(`alpha`)||0,s=i.get(`beta`)||0;t.position.setArray(Q.directionFromAlphaBeta(o,s)),t.lookAt(Q.Vector3.ZERO),t.castShadow=i.get(`shadow`),t.shadowResolution=Q.getShadowResolution(i.get(`shadowQuality`))},updateAmbientCubemap:function(e,t,n){var r=t.getModel(`light.ambientCubemap`),i=r.get(`texture`);if(i){this._cubemapLightsCache=this._cubemapLightsCache||{};var a=this._cubemapLightsCache[i];if(!a){var o=this;a=this._cubemapLightsCache[i]=Q.createAmbientCubemap(r.option,e,n,function(){o._isSkyboxFromAmbientCubemap&&o._skybox.setEnvironmentMap(a.specular.cubemap),n.getZr().refresh()})}this._lightRoot.add(a.diffuse),this._lightRoot.add(a.specular),this._currentCubemapLights=a}else this._currentCubemapLights&&(this._lightRoot.remove(this._currentCubemapLights.diffuse),this._lightRoot.remove(this._currentCubemapLights.specular),this._currentCubemapLights=null)},updateSkybox:function(e,t,n){var r=t.get(`environment`),i=this;function a(){return i._skybox=i._skybox||new Fr,i._skybox}var o=a();if(r&&r!==`none`)if(r===`auto`)if(this._isSkyboxFromAmbientCubemap=!0,this._currentCubemapLights){var s=this._currentCubemapLights.specular.cubemap;o.setEnvironmentMap(s),this._scene&&o.attachScene(this._scene),o.material.set(`lod`,3)}else this._skybox&&this._skybox.detachScene();else if(typeof r==`object`&&r.colorStops||typeof r==`string`&&se(r)){this._isSkyboxFromAmbientCubemap=!1;var c=new Q.Texture2D({anisotropic:8,flipY:!1});o.setEnvironmentMap(c);var l=c.image=document.createElement(`canvas`);l.width=l.height=16,T(l.getContext(`2d`),new A({shape:{x:0,y:0,width:16,height:16},style:{fill:r}})),o.attachScene(this._scene)}else{this._isSkyboxFromAmbientCubemap=!1;var c=Q.loadTexture(r,n,{anisotropic:8,flipY:!1});o.setEnvironmentMap(c),o.attachScene(this._scene)}else this._skybox&&this._skybox.detachScene(this._scene),this._skybox=null;var u=t.coordinateSystem;if(this._skybox)if(u&&u.viewGL&&r!==`auto`&&!(r.match&&r.match(/.hdr$/))){var d=u.viewGL.isLinearSpace()?`define`:`undefine`;this._skybox.material[d](`fragment`,`SRGB_DECODE`)}else this._skybox.material.undefine(`fragment`,`SRGB_DECODE`)}};var Na=Ea.vec3,Pa=Y.extend(function(){return{segmentScale:1,useNativeLine:!0,attributes:{position:new Y.Attribute(`position`,`float`,3,`POSITION`),normal:new Y.Attribute(`normal`,`float`,3,`NORMAL`),color:new Y.Attribute(`color`,`float`,4,`COLOR`)}}},{resetOffset:function(){this._vertexOffset=0,this._faceOffset=0},setQuadCount:function(e){var t=this.attributes,n=this.getQuadVertexCount()*e,r=this.getQuadTriangleCount()*e;this.vertexCount!==n&&(t.position.init(n),t.normal.init(n),t.color.init(n)),this.triangleCount!==r&&(this.indices=n>65535?new Uint32Array(r*3):new Uint16Array(r*3))},getQuadVertexCount:function(){return 4},getQuadTriangleCount:function(){return 2},addQuad:function(){var e=Na.create(),t=Na.create(),n=Na.create(),r=[0,3,1,3,2,1];return function(i,a){var o=this.attributes.position,s=this.attributes.normal,c=this.attributes.color;Na.sub(e,i[1],i[0]),Na.sub(t,i[2],i[1]),Na.cross(n,e,t),Na.normalize(n,n);for(var l=0;l<4;l++)o.set(this._vertexOffset+l,i[l]),c.set(this._vertexOffset+l,a),s.set(this._vertexOffset+l,n);for(var u=this._faceOffset*3,l=0;l<6;l++)this.indices[u+l]=r[l]+this._vertexOffset;this._vertexOffset+=4,this._faceOffset+=2}}()});C(Pa.prototype,Ta);var Fa=X.firstNotNull,Ia={x:0,y:2,z:1};function La(e,t,n,r){var i=[0,0,0],a=r<0?n.getExtentMin():n.getExtentMax();i[Ia[n.dim]]=a,e.position.setArray(i),e.rotation.identity(),t.distance=-Math.abs(a),t.normal.set(0,0,0),n.dim===`x`?(e.rotation.rotateY(r*Math.PI/2),t.normal.x=-r):n.dim===`z`?(e.rotation.rotateX(-r*Math.PI/2),t.normal.y=-r):(r>0&&e.rotation.rotateY(Math.PI),t.normal.z=-r)}function Ra(e,t,n){this.rootNode=new Q.Node;var r=new Q.Mesh({geometry:new ka({useNativeLine:!1}),material:t,castShadow:!1,ignorePicking:!0,$ignorePicking:!0,renderOrder:1}),i=new Q.Mesh({geometry:new Pa,material:n,castShadow:!1,culling:!1,ignorePicking:!0,$ignorePicking:!0,renderOrder:0});this.rootNode.add(i),this.rootNode.add(r),this.faceInfo=e,this.plane=new Q.Plane,this.linesMesh=r,this.quadsMesh=i}Ra.prototype.update=function(e,t,n){var r=e.coordinateSystem,i=[r.getAxis(this.faceInfo[0]),r.getAxis(this.faceInfo[1])],a=this.linesMesh.geometry,o=this.quadsMesh.geometry;a.convertToDynamicArray(!0),o.convertToDynamicArray(!0),this._updateSplitLines(a,i,e,n),this._udpateSplitAreas(o,i,e,n),a.convertToTypedArray(),o.convertToTypedArray();var s=r.getAxis(this.faceInfo[2]);La(this.rootNode,this.plane,s,this.faceInfo[3])},Ra.prototype._updateSplitLines=function(e,t,n,r){var i=r.getDevicePixelRatio();t.forEach(function(r,a){var o=r.model,s=t[1-a].getExtent();if(!r.scale.isBlank()){var c=o.getModel(`splitLine`,n.getModel(`splitLine`));if(c.get(`show`)){var l=c.getModel(`lineStyle`),u=l.get(`color`),d=Fa(l.get(`opacity`),1),f=Fa(l.get(`width`),1);u=F(u)?u:[u];for(var p=r.getTicksCoords({tickModel:c}),m=0,h=0;h<p.length;h++){var g=p[h].coord,_=Q.parseColor(u[m%u.length]);_[3]*=d;var v=[0,0,0],y=[0,0,0];v[a]=y[a]=g,v[1-a]=s[0],y[1-a]=s[1],e.addLine(v,y,_,f*i),m++}}}})},Ra.prototype._udpateSplitAreas=function(e,t,n,r){t.forEach(function(r,i){var a=r.model,o=t[1-i].getExtent();if(!r.scale.isBlank()){var s=a.getModel(`splitArea`,n.getModel(`splitArea`));if(s.get(`show`)){var c=s.getModel(`areaStyle`),l=c.get(`color`),u=Fa(c.get(`opacity`),1);l=F(l)?l:[l];for(var d=r.getTicksCoords({tickModel:s,clamp:!0}),f=0,p=[0,0,0],m=[0,0,0],h=0;h<d.length;h++){var g=d[h].coord,_=[0,0,0],v=[0,0,0];if(_[i]=v[i]=g,_[1-i]=o[0],v[1-i]=o[1],h===0){p=_,m=v;continue}var y=Q.parseColor(l[f%l.length]);y[3]*=u,e.addQuad([p,_,v,m],y),p=_,m=v,f++}}}})};var za=[0,1,2,0,2,3],Ba=Y.extend(function(){return{attributes:{position:new Y.Attribute(`position`,`float`,3,`POSITION`),texcoord:new Y.Attribute(`texcoord`,`float`,2,`TEXCOORD_0`),offset:new Y.Attribute(`offset`,`float`,2),color:new Y.Attribute(`color`,`float`,4,`COLOR`)}}},{resetOffset:function(){this._vertexOffset=0,this._faceOffset=0},setSpriteCount:function(e){this._spriteCount=e;var t=e*4,n=e*2;this.vertexCount!==t&&(this.attributes.position.init(t),this.attributes.offset.init(t),this.attributes.color.init(t)),this.triangleCount!==n&&(this.indices=t>65535?new Uint32Array(n*3):new Uint16Array(n*3))},setSpriteAlign:function(e,t,n,r,i){n==null&&(n=`left`),r==null&&(r=`top`);var a,o,s,c;switch(i=i||0,n){case`left`:a=i,s=t[0]+i;break;case`center`:case`middle`:a=-t[0]/2,s=t[0]/2;break;case`right`:a=-t[0]-i,s=-i;break}switch(r){case`bottom`:o=i,c=t[1]+i;break;case`middle`:o=-t[1]/2,c=t[1]/2;break;case`top`:o=-t[1]-i,c=-i;break}var l=e*4,u=this.attributes.offset;u.set(l,[a,c]),u.set(l+1,[s,c]),u.set(l+2,[s,o]),u.set(l+3,[a,o])},addSprite:function(e,t,n,r,i,a){var o=this._vertexOffset;this.setSprite(this._vertexOffset/4,e,t,n,r,i,a);for(var s=0;s<za.length;s++)this.indices[this._faceOffset*3+s]=za[s]+o;return this._faceOffset+=2,this._vertexOffset+=4,o/4},setSprite:function(e,t,n,r,i,a,o){for(var s=e*4,c=this.attributes,l=0;l<4;l++)c.position.set(s+l,t);var u=c.texcoord;u.set(s,[r[0][0],r[0][1]]),u.set(s+1,[r[1][0],r[0][1]]),u.set(s+2,[r[1][0],r[1][1]]),u.set(s+3,[r[0][0],r[1][1]]),this.setSpriteAlign(e,n,i,a,o)}});C(Ba.prototype,Ta),Q.Shader.import(`@export ecgl.labels.vertex

attribute vec3 position: POSITION;
attribute vec2 texcoord: TEXCOORD_0;
attribute vec2 offset;
#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;

varying vec2 v_Texcoord;

void main()
{
 vec4 proj = worldViewProjection * vec4(position, 1.0);

 vec2 screen = (proj.xy / abs(proj.w) + 1.0) * 0.5 * viewport.zw;

 screen += offset;

 proj.xy = (screen / viewport.zw - 0.5) * 2.0 * abs(proj.w);
 gl_Position = proj;
#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif
 v_Texcoord = texcoord;
}
@end


@export ecgl.labels.fragment

uniform vec3 color : [1.0, 1.0, 1.0];
uniform float alpha : 1.0;
uniform sampler2D textureAtlas;
uniform vec2 uvScale: [1.0, 1.0];

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif
varying float v_Miter;

varying vec2 v_Texcoord;

void main()
{
 gl_FragColor = vec4(color, alpha) * texture2D(textureAtlas, v_Texcoord * uvScale);
#ifdef VERTEX_COLOR
 gl_FragColor *= v_Color;
#endif
}

@end`);var Va=Q.Mesh.extend(function(){return{geometry:new Ba({dynamic:!0}),material:new Q.Material({shader:Q.createShader(`ecgl.labels`),transparent:!0,depthMask:!1}),culling:!1,castShadow:!1,ignorePicking:!0}}),Ha=X.firstNotNull,Ua={x:0,y:2,z:1};function Wa(e,t){var n=new Q.Mesh({geometry:new ka({useNativeLine:!1}),material:t,castShadow:!1,ignorePicking:!0,renderOrder:2}),r=new Va;r.material.depthMask=!1;var i=new Q.Node;i.add(n),i.add(r),this.rootNode=i,this.dim=e,this.linesMesh=n,this.labelsMesh=r,this.axisLineCoords=null,this.labelElements=[]}var Ga={x:`y`,y:`x`,z:`y`};Wa.prototype.update=function(e,n,r){var i=e.coordinateSystem.getAxis(this.dim),a=this.linesMesh.geometry,o=this.labelsMesh.geometry;a.convertToDynamicArray(!0),o.convertToDynamicArray(!0);var s=i.model,c=i.getExtent(),l=r.getDevicePixelRatio(),u=s.getModel(`axisLine`,e.getModel(`axisLine`)),d=s.getModel(`axisTick`,e.getModel(`axisTick`)),f=s.getModel(`axisLabel`,e.getModel(`axisLabel`)),p=u.get(`lineStyle.color`);if(u.get(`show`)){var m=u.getModel(`lineStyle`),h=[0,0,0],g=[0,0,0],_=Ua[i.dim];h[_]=c[0],g[_]=c[1],this.axisLineCoords=[h,g];var v=Q.parseColor(p),y=Ha(m.get(`width`),1),b=Ha(m.get(`opacity`),1);v[3]*=b,a.addLine(h,g,v,y*l)}if(d.get(`show`)){var x=d.getModel(`lineStyle`),S=Q.parseColor(Ha(x.get(`color`),p)),y=Ha(x.get(`width`),1);S[3]*=Ha(x.get(`opacity`),1);for(var C=i.getTicksCoords(),w=d.get(`length`),T=0;T<C.length;T++){var E=C[T].coord,h=[0,0,0],g=[0,0,0],_=Ua[i.dim],D=Ua[Ga[i.dim]];h[_]=g[_]=E,g[D]=w,a.addLine(h,g,S,y*l)}}this.labelElements=[];var l=r.getDevicePixelRatio();if(f.get(`show`))for(var C=i.getTicksCoords(),O=s.get(`data`),k=f.get(`margin`),A=i.getViewLabels(),T=0;T<A.length;T++){var j=t(A[T].tick)?A[T].tick.value:A[T].tickValue,M=A[T].formattedLabel,N=A[T].rawLabel,E=i.dataToCoord(j),ee=[0,0,0],_=Ua[i.dim],D=Ua[Ga[i.dim]];ee[_]=ee[_]=E,ee[D]=k;var te=f;O&&O[j]&&O[j].textStyle&&(te=new _e(O[j].textStyle,f,s.ecModel));var P=Ha(te.get(`color`),p),ne=new re({style:le(te,{text:M,fill:typeof P==`function`?P(i.type===`category`?N:i.type===`value`?j+``:j,T):P,verticalAlign:`top`,align:`left`})}),ie=n.add(ne),ae=ne.getBoundingRect();o.addSprite(ee,[ae.width*l,ae.height*l],ie),this.labelElements.push(ne)}if(s.get(`name`)){var F=s.getModel(`nameTextStyle`),ee=[0,0,0],_=Ua[i.dim],D=Ua[Ga[i.dim]],oe=Ha(F.get(`color`),p),se=F.get(`borderColor`),y=F.get(`borderWidth`);ee[_]=ee[_]=(c[0]+c[1])/2,ee[D]=s.get(`nameGap`);var ne=new re({style:le(F,{text:s.get(`name`),fill:oe,stroke:se,lineWidth:y})}),ie=n.add(ne),ae=ne.getBoundingRect();o.addSprite(ee,[ae.width*l,ae.height*l],ie),ne.__idx=this.labelElements.length,this.nameLabelElement=ne}this.labelsMesh.material.set(`textureAtlas`,n.getTexture()),this.labelsMesh.material.set(`uvScale`,n.getCoordsScale()),a.convertToTypedArray(),o.convertToTypedArray()},Wa.prototype.setSpriteAlign=function(e,t,n){for(var r=n.getDevicePixelRatio(),i=this.labelsMesh.geometry,a=0;a<this.labelElements.length;a++){var o=this.labelElements[a].getBoundingRect();i.setSpriteAlign(a,[o.width*r,o.height*r],e,t)}var s=this.nameLabelElement;if(s){var o=s.getBoundingRect();i.setSpriteAlign(s.__idx,[o.width*r,o.height*r],e,t),i.dirty()}this.textAlign=e,this.textVerticalAlign=t};var Ka=`@export ecgl.lines3D.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

attribute vec3 position: POSITION;
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;

void main()
{
 gl_Position = worldViewProjection * vec4(position, 1.0);
 v_Color = a_Color;
}

@end

@export ecgl.lines3D.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

varying vec4 v_Color;

@import clay.util.srgb

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color * v_Color);
#else
 gl_FragColor = color * v_Color;
#endif
}
@end



@export ecgl.lines3D.clipNear

vec4 clipNear(vec4 p1, vec4 p2) {
 float n = (p1.w - near) / (p1.w - p2.w);
 return vec4(mix(p1.xy, p2.xy, n), -near, near);
}

@end

@export ecgl.lines3D.expandLine
#ifdef VERTEX_ANIMATION
 vec4 prevProj = worldViewProjection * vec4(mix(prevPositionPrev, positionPrev, percent), 1.0);
 vec4 currProj = worldViewProjection * vec4(mix(prevPosition, position, percent), 1.0);
 vec4 nextProj = worldViewProjection * vec4(mix(prevPositionNext, positionNext, percent), 1.0);
#else
 vec4 prevProj = worldViewProjection * vec4(positionPrev, 1.0);
 vec4 currProj = worldViewProjection * vec4(position, 1.0);
 vec4 nextProj = worldViewProjection * vec4(positionNext, 1.0);
#endif

 if (currProj.w < 0.0) {
 if (nextProj.w > 0.0) {
 currProj = clipNear(currProj, nextProj);
 }
 else if (prevProj.w > 0.0) {
 currProj = clipNear(currProj, prevProj);
 }
 }

 vec2 prevScreen = (prevProj.xy / abs(prevProj.w) + 1.0) * 0.5 * viewport.zw;
 vec2 currScreen = (currProj.xy / abs(currProj.w) + 1.0) * 0.5 * viewport.zw;
 vec2 nextScreen = (nextProj.xy / abs(nextProj.w) + 1.0) * 0.5 * viewport.zw;

 vec2 dir;
 float len = offset;
 if (position == positionPrev) {
 dir = normalize(nextScreen - currScreen);
 }
 else if (position == positionNext) {
 dir = normalize(currScreen - prevScreen);
 }
 else {
 vec2 dirA = normalize(currScreen - prevScreen);
 vec2 dirB = normalize(nextScreen - currScreen);

 vec2 tanget = normalize(dirA + dirB);

 float miter = 1.0 / max(dot(tanget, dirA), 0.5);
 len *= miter;
 dir = tanget;
 }

 dir = vec2(-dir.y, dir.x) * len;
 currScreen += dir;

 currProj.xy = (currScreen / viewport.zw - 0.5) * 2.0 * abs(currProj.w);
@end


@export ecgl.meshLines3D.vertex

attribute vec3 position: POSITION;
attribute vec3 positionPrev;
attribute vec3 positionNext;
attribute float offset;
attribute vec4 a_Color : COLOR;

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
attribute vec3 prevPositionPrev;
attribute vec3 prevPositionNext;
uniform float percent : 1.0;
#endif

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;
uniform float near : NEAR;

varying vec4 v_Color;

@import ecgl.common.wireframe.vertexHeader

@import ecgl.lines3D.clipNear

void main()
{
 @import ecgl.lines3D.expandLine

 gl_Position = currProj;

 v_Color = a_Color;

 @import ecgl.common.wireframe.vertexMain
}
@end


@export ecgl.meshLines3D.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

varying vec4 v_Color;

@import ecgl.common.wireframe.fragmentHeader

@import clay.util.srgb

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color * v_Color);
#else
 gl_FragColor = color * v_Color;
#endif

 @import ecgl.common.wireframe.fragmentMain
}

@end`,qa=X.firstNotNull;Q.Shader.import(Ka);var Ja={x:0,y:2,z:1},Ya=fe.extend({type:`grid3D`,__ecgl__:!0,init:function(e,t){var n=[[`y`,`z`,`x`,-1,`left`],[`y`,`z`,`x`,1,`right`],[`x`,`y`,`z`,-1,`bottom`],[`x`,`y`,`z`,1,`top`],[`x`,`z`,`y`,-1,`far`],[`x`,`z`,`y`,1,`near`]],r=[`x`,`y`,`z`],i=new Q.Material({shader:Q.createShader(`ecgl.color`),depthMask:!1,transparent:!0}),a=new Q.Material({shader:Q.createShader(`ecgl.meshLines3D`),depthMask:!1,transparent:!0});i.define(`fragment`,`DOUBLE_SIDED`),i.define(`both`,`VERTEX_COLOR`),this.groupGL=new Q.Node,this._control=new wa({zr:t.getZr()}),this._control.init(),this._faces=n.map(function(e){var t=new Ra(e,a,i);return this.groupGL.add(t.rootNode),t},this),this._axes=r.map(function(e){var t=new Wa(e,a);return this.groupGL.add(t.rootNode),t},this);var o=t.getDevicePixelRatio();this._axisLabelSurface=new ja({width:256,height:256,devicePixelRatio:o}),this._axisLabelSurface.onupdate=function(){t.getZr().refresh()},this._axisPointerLineMesh=new Q.Mesh({geometry:new ka({useNativeLine:!1}),material:a,castShadow:!1,ignorePicking:!0,renderOrder:3}),this.groupGL.add(this._axisPointerLineMesh),this._axisPointerLabelsSurface=new ja({width:128,height:128,devicePixelRatio:o}),this._axisPointerLabelsMesh=new Va({ignorePicking:!0,renderOrder:4,castShadow:!1}),this._axisPointerLabelsMesh.material.set(`textureAtlas`,this._axisPointerLabelsSurface.getTexture()),this.groupGL.add(this._axisPointerLabelsMesh),this._lightRoot=new Q.Node,this._sceneHelper=new Ma,this._sceneHelper.initLight(this._lightRoot)},render:function(e,t,n){this._model=e,this._api=n;var r=e.coordinateSystem;r.viewGL.add(this._lightRoot),e.get(`show`)?r.viewGL.add(this.groupGL):r.viewGL.remove(this.groupGL);var i=this._control;i.setViewGL(r.viewGL);var a=e.getModel(`viewControl`);i.setFromViewControlModel(a,0),this._axisLabelSurface.clear(),i.off(`update`),e.get(`show`)&&(this._faces.forEach(function(r){r.update(e,t,n)},this),this._axes.forEach(function(t){t.update(e,this._axisLabelSurface,n)},this)),i.on(`update`,this._onCameraChange.bind(this,e,n),this),this._sceneHelper.setScene(r.viewGL.scene),this._sceneHelper.updateLight(e),r.viewGL.setPostEffect(e.getModel(`postEffect`),n),r.viewGL.setTemporalSuperSampling(e.getModel(`temporalSuperSampling`)),this._initMouseHandler(e)},afterRender:function(e,t,n,r){var i=r.renderer;this._sceneHelper.updateAmbientCubemap(i,e,n),this._sceneHelper.updateSkybox(i,e,n)},showAxisPointer:function(e,t,n,r){this._doShowAxisPointer(),this._updateAxisPointer(r.value)},hideAxisPointer:function(e,t,n,r){this._doHideAxisPointer()},_initMouseHandler:function(e){var t=e.coordinateSystem.viewGL;e.get(`show`)&&e.get(`axisPointer.show`)?t.on(`mousemove`,this._updateAxisPointerOnMousePosition,this):t.off(`mousemove`,this._updateAxisPointerOnMousePosition)},_updateAxisPointerOnMousePosition:function(e){if(!e.target){for(var t=this._model.coordinateSystem,n=t.viewGL,r=n.castRay(e.offsetX,e.offsetY,new Q.Ray),i,a=0;a<this._faces.length;a++){var o=this._faces[a];if(!o.rootNode.invisible){o.plane.normal.dot(n.camera.worldTransform.z)<0&&o.plane.normal.negate();var s=r.intersectPlane(o.plane);if(s){var c=t.getAxis(o.faceInfo[0]),l=t.getAxis(o.faceInfo[1]),u=Ja[o.faceInfo[0]],d=Ja[o.faceInfo[1]];c.contain(s.array[u])&&l.contain(s.array[d])&&(i=s)}}}if(i){var f=t.pointToData(i.array,[],!0);this._updateAxisPointer(f),this._doShowAxisPointer()}else this._doHideAxisPointer()}},_onCameraChange:function(e,t){e.get(`show`)&&(this._updateFaceVisibility(),this._updateAxisLinePosition());var n=this._control;t.dispatchAction({type:`grid3DChangeCamera`,alpha:n.getAlpha(),beta:n.getBeta(),distance:n.getDistance(),center:n.getCenter(),from:this.uid,grid3DId:e.id})},_updateFaceVisibility:function(){var e=this._control.getCamera(),t=new Q.Vector3;e.update();for(var n=0;n<this._faces.length/2;n++){for(var r=[],i=0;i<2;i++)this._faces[n*2+i].rootNode.getWorldPosition(t),t.transformMat4(e.viewMatrix),r[i]=t.z;var a=r[0]>r[1]?0:1,o=this._faces[n*2+a],s=this._faces[n*2+1-a];o.rootNode.invisible=!0,s.rootNode.invisible=!1}},_updateAxisLinePosition:function(){var e=this._model.coordinateSystem,t=e.getAxis(`x`),n=e.getAxis(`y`),r=e.getAxis(`z`),i=r.getExtentMax(),a=r.getExtentMin(),o=t.getExtentMin(),s=t.getExtentMax(),c=n.getExtentMax(),l=n.getExtentMin(),u=this._axes[0].rootNode,d=this._axes[1].rootNode,f=this._axes[2].rootNode,p=this._faces,m=p[4].rootNode.invisible?l:c,h=p[2].rootNode.invisible?i:a,g=p[0].rootNode.invisible?o:s,_=p[2].rootNode.invisible?i:a,v=p[0].rootNode.invisible?s:o,y=p[4].rootNode.invisible?l:c;u.rotation.identity(),d.rotation.identity(),f.rotation.identity(),p[4].rootNode.invisible&&(this._axes[0].flipped=!0,u.rotation.rotateX(Math.PI)),p[0].rootNode.invisible&&(this._axes[1].flipped=!0,d.rotation.rotateZ(Math.PI)),p[4].rootNode.invisible&&(this._axes[2].flipped=!0,f.rotation.rotateY(Math.PI)),u.position.set(0,h,m),d.position.set(g,_,0),f.position.set(v,0,y),u.update(),d.update(),f.update(),this._updateAxisLabelAlign()},_updateAxisLabelAlign:function(){var e=this._control.getCamera(),t=[new Q.Vector4,new Q.Vector4],n=new Q.Vector4;this.groupGL.getWorldPosition(n),n.w=1,n.transformMat4(e.viewMatrix).transformMat4(e.projectionMatrix),n.x/=n.w,n.y/=n.w,this._axes.forEach(function(r){var i=r.axisLineCoords;r.labelsMesh.geometry;for(var a=0;a<t.length;a++)t[a].setArray(i[a]),t[a].w=1,t[a].transformMat4(r.rootNode.worldTransform).transformMat4(e.viewMatrix).transformMat4(e.projectionMatrix),t[a].x/=t[a].w,t[a].y/=t[a].w;var o=t[1].x-t[0].x,s=t[1].y-t[0].y,c=(t[1].x+t[0].x)/2,l=(t[1].y+t[0].y)/2,u,d;Math.abs(s/o)<.5?(u=`center`,d=l>n.y?`bottom`:`top`):(d=`middle`,u=c>n.x?`left`:`right`),r.setSpriteAlign(u,d,this._api)},this)},_doShowAxisPointer:function(){this._axisPointerLineMesh.invisible&&(this._axisPointerLineMesh.invisible=!1,this._axisPointerLabelsMesh.invisible=!1,this._api.getZr().refresh())},_doHideAxisPointer:function(){this._axisPointerLineMesh.invisible||(this._axisPointerLineMesh.invisible=!0,this._axisPointerLabelsMesh.invisible=!0,this._api.getZr().refresh())},_updateAxisPointer:function(e){var t=this._model.coordinateSystem,n=t.dataToPoint(e),r=this._axisPointerLineMesh.geometry,i=this._model.getModel(`axisPointer`),a=this._api.getDevicePixelRatio();r.convertToDynamicArray(!0);function o(e){return X.firstNotNull(e.model.get(`axisPointer.show`),i.get(`show`))}function s(e){var t=e.model.getModel(`axisPointer`,i).getModel(`lineStyle`),n=Q.parseColor(t.get(`color`)),r=qa(t.get(`width`),1),a=qa(t.get(`opacity`),1);return n[3]*=a,{color:n,lineWidth:r}}for(var c=0;c<this._faces.length;c++){var l=this._faces[c];if(!l.rootNode.invisible){for(var u=l.faceInfo,d=u[3]<0?t.getAxis(u[2]).getExtentMin():t.getAxis(u[2]).getExtentMax(),f=Ja[u[2]],p=0;p<2;p++){var m=u[p],h=u[1-p],g=t.getAxis(m),_=t.getAxis(h);if(o(g)){var v=[0,0,0],y=[0,0,0],b=Ja[m],x=Ja[h];v[b]=y[b]=n[b],v[f]=y[f]=d,v[x]=_.getExtentMin(),y[x]=_.getExtentMax();var S=s(g);r.addLine(v,y,S.color,S.lineWidth*a)}}if(o(t.getAxis(u[2]))){var v=n.slice(),y=n.slice();y[f]=d;var S=s(t.getAxis(u[2]));r.addLine(v,y,S.color,S.lineWidth*a)}}}r.convertToTypedArray(),this._updateAxisPointerLabelsMesh(e),this._api.getZr().refresh()},_updateAxisPointerLabelsMesh:function(e){var t=this._model,n=this._axisPointerLabelsMesh,r=this._axisPointerLabelsSurface,i=t.coordinateSystem,a=t.getModel(`axisPointer`);n.geometry.convertToDynamicArray(!0),r.clear();var o={x:`y`,y:`x`,z:`y`};this._axes.forEach(function(t,s){var c=i.getAxis(t.dim),l=c.model.getModel(`axisPointer`,a),u=l.getModel(`label`),d=l.get(`lineStyle.color`);if(!(!u.get(`show`)||!l.get(`show`))){var f=e[s],p=u.get(`formatter`),m=c.scale.getLabel({value:f});if(p!=null)m=p(m,e);else if(c.scale.type===`interval`||c.scale.type===`log`){var h=he(c.scale.getTicks()[0]);m=f.toFixed(h+2)}var g=u.get(`color`),_=new re({style:le(u,{text:m,fill:g||d,align:`left`,verticalAlign:`top`})}),v=r.add(_),y=_.getBoundingRect(),b=this._api.getDevicePixelRatio(),x=t.rootNode.position.toArray(),S=Ja[o[t.dim]];x[S]+=(t.flipped?-1:1)*u.get(`margin`),x[Ja[t.dim]]=c.dataToCoord(e[s]),n.geometry.addSprite(x,[y.width*b,y.height*b],v,t.textAlign,t.textVerticalAlign)}},this),r.getZr().refreshImmediately(),n.material.set(`uvScale`,r.getCoordsScale()),n.geometry.convertToTypedArray()},dispose:function(){this.groupGL.removeAll(),this._control.dispose(),this._axisLabelSurface.dispose(),this._axisPointerLabelsSurface.dispose()}});function Xa(e){S.call(this,e),this.type=`cartesian3D`,this.dimensions=[`x`,`y`,`z`],this.size=[0,0,0]}Xa.prototype={constructor:Xa,model:null,containPoint:function(e){return this.getAxis(`x`).contain(e[0])&&this.getAxis(`y`).contain(e[2])&&this.getAxis(`z`).contain(e[1])},containData:function(e){return this.getAxis(`x`).containData(e[0])&&this.getAxis(`y`).containData(e[1])&&this.getAxis(`z`).containData(e[2])},dataToPoint:function(e,t,n){return t=t||[],t[0]=this.getAxis(`x`).dataToCoord(e[0],n),t[2]=this.getAxis(`y`).dataToCoord(e[1],n),t[1]=this.getAxis(`z`).dataToCoord(e[2],n),t},pointToData:function(e,t,n){return t=t||[],t[0]=this.getAxis(`x`).coordToData(e[0],n),t[1]=this.getAxis(`y`).coordToData(e[2],n),t[2]=this.getAxis(`z`).coordToData(e[1],n),t}},_(Xa,S);function Za(e,t,n){ie.call(this,e,t,n)}Za.prototype={constructor:Za,getExtentMin:function(){var e=this._extent;return Math.min(e[0],e[1])},getExtentMax:function(){var e=this._extent;return Math.max(e[0],e[1])},calculateCategoryInterval:function(){return Math.floor(this.scale.count()/8)}},_(Za,ie);var Qa=function(){this._pool={},this._allocatedTextures=[]};Qa.prototype={constructor:Qa,get:function(e){var t=to(e);this._pool.hasOwnProperty(t)||(this._pool[t]=[]);var n=this._pool[t];if(!n.length){var r=new J(e);return this._allocatedTextures.push(r),r}return n.pop()},put:function(e){var t=to(e);this._pool.hasOwnProperty(t)||(this._pool[t]=[]),this._pool[t].push(e)},clear:function(e){for(var t=0;t<this._allocatedTextures.length;t++)this._allocatedTextures[t].dispose(e);this._pool={},this._allocatedTextures=[]}};var $a={width:512,height:512,type:U.UNSIGNED_BYTE,format:U.RGBA,wrapS:U.CLAMP_TO_EDGE,wrapT:U.CLAMP_TO_EDGE,minFilter:U.LINEAR_MIPMAP_LINEAR,magFilter:U.LINEAR,useMipmap:!0,anisotropic:1,flipY:!0,unpackAlignment:4,premultiplyAlpha:!1},eo=Object.keys($a);function to(e){Pe.defaultsWithPropList(e,$a,eo),no(e);for(var t=``,n=0;n<eo.length;n++){var r=e[eo[n]].toString();t+=r}return t}function no(e){var t=ro(e.width,e.height);e.format===U.DEPTH_COMPONENT&&(e.useMipmap=!1),(!t||!e.useMipmap)&&(e.minFilter==U.NEAREST_MIPMAP_NEAREST||e.minFilter==U.NEAREST_MIPMAP_LINEAR?e.minFilter=U.NEAREST:(e.minFilter==U.LINEAR_MIPMAP_LINEAR||e.minFilter==U.LINEAR_MIPMAP_NEAREST)&&(e.minFilter=U.LINEAR)),t||(e.wrapS=U.CLAMP_TO_EDGE,e.wrapT=U.CLAMP_TO_EDGE)}function ro(e,t){return(e&e-1)==0&&(t&t-1)==0}var io=`@export clay.sm.depth.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;
uniform vec2 uvRepeat = vec2(1.0, 1.0);
uniform vec2 uvOffset = vec2(0.0, 0.0);
@import clay.chunk.skinning_header
@import clay.chunk.instancing_header
varying vec4 v_ViewPosition;
varying vec2 v_Texcoord;
void main(){
 vec4 P = vec4(position, 1.0);
#ifdef SKINNING
 @import clay.chunk.skin_matrix
 P = skinMatrixWS * P;
#endif
#ifdef INSTANCING
 @import clay.chunk.instancing_matrix
 P = instanceMat * P;
#endif
 v_ViewPosition = worldViewProjection * P;
 gl_Position = v_ViewPosition;
 v_Texcoord = texcoord * uvRepeat + uvOffset;
}
@end
@export clay.sm.depth.fragment
varying vec4 v_ViewPosition;
varying vec2 v_Texcoord;
uniform float bias : 0.001;
uniform float slopeScale : 1.0;
uniform sampler2D alphaMap;
uniform float alphaCutoff: 0.0;
@import clay.util.encode_float
void main(){
 float depth = v_ViewPosition.z / v_ViewPosition.w;
 if (alphaCutoff > 0.0) {
 if (texture2D(alphaMap, v_Texcoord).a <= alphaCutoff) {
 discard;
 }
 }
#ifdef USE_VSM
 depth = depth * 0.5 + 0.5;
 float moment1 = depth;
 float moment2 = depth * depth;
 #ifdef SUPPORT_STANDARD_DERIVATIVES
 float dx = dFdx(depth);
 float dy = dFdy(depth);
 moment2 += 0.25*(dx*dx+dy*dy);
 #endif
 gl_FragColor = vec4(moment1, moment2, 0.0, 1.0);
#else
 #ifdef SUPPORT_STANDARD_DERIVATIVES
 float dx = dFdx(depth);
 float dy = dFdy(depth);
 depth += sqrt(dx*dx + dy*dy) * slopeScale + bias;
 #else
 depth += bias;
 #endif
 gl_FragColor = encodeFloat(depth * 0.5 + 0.5);
#endif
}
@end
@export clay.sm.debug_depth
uniform sampler2D depthMap;
varying vec2 v_Texcoord;
@import clay.util.decode_float
void main() {
 vec4 tex = texture2D(depthMap, v_Texcoord);
#ifdef USE_VSM
 gl_FragColor = vec4(tex.rgb, 1.0);
#else
 float depth = decodeFloat(tex);
 gl_FragColor = vec4(depth, depth, depth, 1.0);
#endif
}
@end
@export clay.sm.distance.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform mat4 world : WORLD;
attribute vec3 position : POSITION;
@import clay.chunk.skinning_header
varying vec3 v_WorldPosition;
void main (){
 vec4 P = vec4(position, 1.0);
#ifdef SKINNING
 @import clay.chunk.skin_matrix
 P = skinMatrixWS * P;
#endif
#ifdef INSTANCING
 @import clay.chunk.instancing_matrix
 P = instanceMat * P;
#endif
 gl_Position = worldViewProjection * P;
 v_WorldPosition = (world * P).xyz;
}
@end
@export clay.sm.distance.fragment
uniform vec3 lightPosition;
uniform float range : 100;
varying vec3 v_WorldPosition;
@import clay.util.encode_float
void main(){
 float dist = distance(lightPosition, v_WorldPosition);
#ifdef USE_VSM
 gl_FragColor = vec4(dist, dist * dist, 0.0, 0.0);
#else
 dist = dist / range;
 gl_FragColor = encodeFloat(dist);
#endif
}
@end
@export clay.plugin.shadow_map_common
@import clay.util.decode_float
float tapShadowMap(sampler2D map, vec2 uv, float z){
 vec4 tex = texture2D(map, uv);
 return step(z, decodeFloat(tex) * 2.0 - 1.0);
}
float pcf(sampler2D map, vec2 uv, float z, float textureSize, vec2 scale) {
 float shadowContrib = tapShadowMap(map, uv, z);
 vec2 offset = vec2(1.0 / textureSize) * scale;
#ifdef PCF_KERNEL_SIZE
 for (int _idx_ = 0; _idx_ < PCF_KERNEL_SIZE; _idx_++) {{
 shadowContrib += tapShadowMap(map, uv + offset * pcfKernel[_idx_], z);
 }}
 return shadowContrib / float(PCF_KERNEL_SIZE + 1);
#else
 shadowContrib += tapShadowMap(map, uv+vec2(offset.x, 0.0), z);
 shadowContrib += tapShadowMap(map, uv+vec2(offset.x, offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(-offset.x, offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(0.0, offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(-offset.x, 0.0), z);
 shadowContrib += tapShadowMap(map, uv+vec2(-offset.x, -offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(offset.x, -offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(0.0, -offset.y), z);
 return shadowContrib / 9.0;
#endif
}
float pcf(sampler2D map, vec2 uv, float z, float textureSize) {
 return pcf(map, uv, z, textureSize, vec2(1.0));
}
float chebyshevUpperBound(vec2 moments, float z){
 float p = 0.0;
 z = z * 0.5 + 0.5;
 if (z <= moments.x) {
 p = 1.0;
 }
 float variance = moments.y - moments.x * moments.x;
 variance = max(variance, 0.0000001);
 float mD = moments.x - z;
 float pMax = variance / (variance + mD * mD);
 pMax = clamp((pMax-0.4)/(1.0-0.4), 0.0, 1.0);
 return max(p, pMax);
}
float computeShadowContrib(
 sampler2D map, mat4 lightVPM, vec3 position, float textureSize, vec2 scale, vec2 offset
) {
 vec4 posInLightSpace = lightVPM * vec4(position, 1.0);
 posInLightSpace.xyz /= posInLightSpace.w;
 float z = posInLightSpace.z;
 if(all(greaterThan(posInLightSpace.xyz, vec3(-0.99, -0.99, -1.0))) &&
 all(lessThan(posInLightSpace.xyz, vec3(0.99, 0.99, 1.0)))){
 vec2 uv = (posInLightSpace.xy+1.0) / 2.0;
 #ifdef USE_VSM
 vec2 moments = texture2D(map, uv * scale + offset).xy;
 return chebyshevUpperBound(moments, z);
 #else
 return pcf(map, uv * scale + offset, z, textureSize, scale);
 #endif
 }
 return 1.0;
}
float computeShadowContrib(sampler2D map, mat4 lightVPM, vec3 position, float textureSize) {
 return computeShadowContrib(map, lightVPM, position, textureSize, vec2(1.0), vec2(0.0));
}
float computeShadowContribOmni(samplerCube map, vec3 direction, float range)
{
 float dist = length(direction);
 vec4 shadowTex = textureCube(map, direction);
#ifdef USE_VSM
 vec2 moments = shadowTex.xy;
 float variance = moments.y - moments.x * moments.x;
 float mD = moments.x - dist;
 float p = variance / (variance + mD * mD);
 if(moments.x + 0.001 < dist){
 return clamp(p, 0.0, 1.0);
 }else{
 return 1.0;
 }
#else
 return step(dist, (decodeFloat(shadowTex) + 0.0002) * range);
#endif
}
@end
@export clay.plugin.compute_shadow_map
#if defined(SPOT_LIGHT_SHADOWMAP_COUNT) || defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT) || defined(POINT_LIGHT_SHADOWMAP_COUNT)
#ifdef SPOT_LIGHT_SHADOWMAP_COUNT
uniform sampler2D spotLightShadowMaps[SPOT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform mat4 spotLightMatrices[SPOT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform float spotLightShadowMapSizes[SPOT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
#endif
#ifdef DIRECTIONAL_LIGHT_SHADOWMAP_COUNT
#if defined(SHADOW_CASCADE)
uniform sampler2D directionalLightShadowMaps[1]:unconfigurable;
uniform mat4 directionalLightMatrices[SHADOW_CASCADE]:unconfigurable;
uniform float directionalLightShadowMapSizes[1]:unconfigurable;
uniform float shadowCascadeClipsNear[SHADOW_CASCADE]:unconfigurable;
uniform float shadowCascadeClipsFar[SHADOW_CASCADE]:unconfigurable;
#else
uniform sampler2D directionalLightShadowMaps[DIRECTIONAL_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform mat4 directionalLightMatrices[DIRECTIONAL_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform float directionalLightShadowMapSizes[DIRECTIONAL_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
#endif
#endif
#ifdef POINT_LIGHT_SHADOWMAP_COUNT
uniform samplerCube pointLightShadowMaps[POINT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
#endif
uniform bool shadowEnabled : true;
#ifdef PCF_KERNEL_SIZE
uniform vec2 pcfKernel[PCF_KERNEL_SIZE];
#endif
@import clay.plugin.shadow_map_common
#if defined(SPOT_LIGHT_SHADOWMAP_COUNT)
void computeShadowOfSpotLights(vec3 position, inout float shadowContribs[SPOT_LIGHT_COUNT] ) {
 float shadowContrib;
 for(int _idx_ = 0; _idx_ < SPOT_LIGHT_SHADOWMAP_COUNT; _idx_++) {{
 shadowContrib = computeShadowContrib(
 spotLightShadowMaps[_idx_], spotLightMatrices[_idx_], position,
 spotLightShadowMapSizes[_idx_]
 );
 shadowContribs[_idx_] = shadowContrib;
 }}
 for(int _idx_ = SPOT_LIGHT_SHADOWMAP_COUNT; _idx_ < SPOT_LIGHT_COUNT; _idx_++){{
 shadowContribs[_idx_] = 1.0;
 }}
}
#endif
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
#ifdef SHADOW_CASCADE
void computeShadowOfDirectionalLights(vec3 position, inout float shadowContribs[DIRECTIONAL_LIGHT_COUNT]){
 float depth = (2.0 * gl_FragCoord.z - gl_DepthRange.near - gl_DepthRange.far)
 / (gl_DepthRange.far - gl_DepthRange.near);
 float shadowContrib;
 shadowContribs[0] = 1.0;
 for (int _idx_ = 0; _idx_ < SHADOW_CASCADE; _idx_++) {{
 if (
 depth >= shadowCascadeClipsNear[_idx_] &&
 depth <= shadowCascadeClipsFar[_idx_]
 ) {
 shadowContrib = computeShadowContrib(
 directionalLightShadowMaps[0], directionalLightMatrices[_idx_], position,
 directionalLightShadowMapSizes[0],
 vec2(1.0 / float(SHADOW_CASCADE), 1.0),
 vec2(float(_idx_) / float(SHADOW_CASCADE), 0.0)
 );
 shadowContribs[0] = shadowContrib;
 }
 }}
 for(int _idx_ = DIRECTIONAL_LIGHT_SHADOWMAP_COUNT; _idx_ < DIRECTIONAL_LIGHT_COUNT; _idx_++) {{
 shadowContribs[_idx_] = 1.0;
 }}
}
#else
void computeShadowOfDirectionalLights(vec3 position, inout float shadowContribs[DIRECTIONAL_LIGHT_COUNT]){
 float shadowContrib;
 for(int _idx_ = 0; _idx_ < DIRECTIONAL_LIGHT_SHADOWMAP_COUNT; _idx_++) {{
 shadowContrib = computeShadowContrib(
 directionalLightShadowMaps[_idx_], directionalLightMatrices[_idx_], position,
 directionalLightShadowMapSizes[_idx_]
 );
 shadowContribs[_idx_] = shadowContrib;
 }}
 for(int _idx_ = DIRECTIONAL_LIGHT_SHADOWMAP_COUNT; _idx_ < DIRECTIONAL_LIGHT_COUNT; _idx_++) {{
 shadowContribs[_idx_] = 1.0;
 }}
}
#endif
#endif
#if defined(POINT_LIGHT_SHADOWMAP_COUNT)
void computeShadowOfPointLights(vec3 position, inout float shadowContribs[POINT_LIGHT_COUNT] ){
 vec3 lightPosition;
 vec3 direction;
 for(int _idx_ = 0; _idx_ < POINT_LIGHT_SHADOWMAP_COUNT; _idx_++) {{
 lightPosition = pointLightPosition[_idx_];
 direction = position - lightPosition;
 shadowContribs[_idx_] = computeShadowContribOmni(pointLightShadowMaps[_idx_], direction, pointLightRange[_idx_]);
 }}
 for(int _idx_ = POINT_LIGHT_SHADOWMAP_COUNT; _idx_ < POINT_LIGHT_COUNT; _idx_++) {{
 shadowContribs[_idx_] = 1.0;
 }}
}
#endif
#endif
@end`,ao=[`px`,`nx`,`py`,`ny`,`pz`,`nz`];K.import(io);function oo(e,t,n){return n===`alphaMap`?e.material.get(`diffuseMap`):n===`alphaCutoff`?e.material.isDefined(`fragment`,`ALPHA_TEST`)&&e.material.get(`diffuseMap`)&&e.material.get(`alphaCutoff`)||0:n===`uvRepeat`?e.material.get(`uvRepeat`):n===`uvOffset`?e.material.get(`uvOffset`):t.get(n)}function so(e,t){var n=e.material,r=t.material;return n.get(`diffuseMap`)!==r.get(`diffuseMap`)||(n.get(`alphaCutoff`)||0)!==(r.get(`alphaCutoff`)||0)}var co=Fe.extend(function(){return{softShadow:co.PCF,shadowBlur:1,lightFrustumBias:`auto`,kernelPCF:new Float32Array([1,0,1,1,-1,1,0,1,-1,0,-1,-1,1,-1,0,-1]),precision:`highp`,_lastRenderNotCastShadow:!1,_frameBuffer:new Or,_textures:{},_shadowMapNumber:{POINT_LIGHT:0,DIRECTIONAL_LIGHT:0,SPOT_LIGHT:0},_depthMaterials:{},_distanceMaterials:{},_receivers:[],_lightsCastShadow:[],_lightCameras:{},_lightMaterials:{},_texturePool:new Qa}},function(){this._gaussianPassH=new bi({fragment:K.source(`clay.compositor.gaussian_blur`)}),this._gaussianPassV=new bi({fragment:K.source(`clay.compositor.gaussian_blur`)}),this._gaussianPassH.setUniform(`blurSize`,this.shadowBlur),this._gaussianPassH.setUniform(`blurDir`,0),this._gaussianPassV.setUniform(`blurSize`,this.shadowBlur),this._gaussianPassV.setUniform(`blurDir`,1),this._outputDepthPass=new bi({fragment:K.source(`clay.sm.debug_depth`)})},{render:function(e,t,n,r){n||(n=t.getMainCamera()),this.trigger(`beforerender`,this,e,t,n),this._renderShadowPass(e,t,n,r),this.trigger(`afterrender`,this,e,t,n)},renderDebug:function(e,t){e.saveClear();var n=e.viewport,r=0,i=0,a=t||n.width/4,o=a;for(var s in this.softShadow===co.VSM?this._outputDepthPass.material.define(`fragment`,`USE_VSM`):this._outputDepthPass.material.undefine(`fragment`,`USE_VSM`),this._textures){var c=this._textures[s];e.setViewport(r,i,a*c.width/c.height,o),this._outputDepthPass.setUniform(`depthMap`,c),this._outputDepthPass.render(e),r+=a*c.width/c.height}e.setViewport(n),e.restoreClear()},_updateReceivers:function(e,t){if(t.receiveShadow?(this._receivers.push(t),t.material.set(`shadowEnabled`,1),t.material.set(`pcfKernel`,this.kernelPCF)):t.material.set(`shadowEnabled`,0),this.softShadow===co.VSM)t.material.define(`fragment`,`USE_VSM`),t.material.undefine(`fragment`,`PCF_KERNEL_SIZE`);else{t.material.undefine(`fragment`,`USE_VSM`);var n=this.kernelPCF;n&&n.length?t.material.define(`fragment`,`PCF_KERNEL_SIZE`,n.length/2):t.material.undefine(`fragment`,`PCF_KERNEL_SIZE`)}},_update:function(e,t){var n=this;t.traverse(function(t){t.isRenderable()&&n._updateReceivers(e,t)});for(var r=0;r<t.lights.length;r++){var i=t.lights[r];i.castShadow&&!i.invisible&&this._lightsCastShadow.push(i)}},_renderShadowPass:function(e,t,n,r){for(var i in this._shadowMapNumber)this._shadowMapNumber[i]=0;this._lightsCastShadow.length=0,this._receivers.length=0;var a=e.gl;if(r||t.update(),n&&n.update(),t.updateLights(),this._update(e,t),!this._lightsCastShadow.length&&this._lastRenderNotCastShadow)return;this._lastRenderNotCastShadow=this._lightsCastShadow===0,a.enable(a.DEPTH_TEST),a.depthMask(!0),a.disable(a.BLEND),a.clearColor(1,1,1,1);for(var o=[],s=[],c=[],l=[],u=[],d=[],f,p=0;p<this._lightsCastShadow.length;p++){var m=this._lightsCastShadow[p];if(m.type===`DIRECTIONAL_LIGHT`){if(f){console.warn(`Only one direectional light supported with shadow cascade`);continue}if(m.shadowCascade>4){console.warn(`Support at most 4 cascade`);continue}m.shadowCascade>1&&(f=m),this.renderDirectionalLightShadow(e,t,n,m,u,l,c)}else m.type===`SPOT_LIGHT`?this.renderSpotLightShadow(e,t,m,s,o):m.type===`POINT_LIGHT`&&this.renderPointLightShadow(e,t,m,d);this._shadowMapNumber[m.type]++}for(var h in this._shadowMapNumber)for(var g=this._shadowMapNumber[h],_=h+`_SHADOWMAP_COUNT`,p=0;p<this._receivers.length;p++){var v=this._receivers[p],y=v.material;y.fragmentDefines[_]!==g&&(g>0?y.define(`fragment`,_,g):y.isDefined(`fragment`,_)&&y.undefine(`fragment`,_))}for(var p=0;p<this._receivers.length;p++){var v=this._receivers[p],y=v.material;f?y.define(`fragment`,`SHADOW_CASCADE`,f.shadowCascade):y.undefine(`fragment`,`SHADOW_CASCADE`)}var b=t.shadowUniforms;function x(e){return e.height}if(c.length>0){var S=c.map(x);if(b.directionalLightShadowMaps={value:c,type:`tv`},b.directionalLightMatrices={value:l,type:`m4v`},b.directionalLightShadowMapSizes={value:S,type:`1fv`},f){var C=u.slice(),w=u.slice();C.pop(),w.shift(),C.reverse(),w.reverse(),l.reverse(),b.shadowCascadeClipsNear={value:C,type:`1fv`},b.shadowCascadeClipsFar={value:w,type:`1fv`}}}if(o.length>0){var T=o.map(x),b=t.shadowUniforms;b.spotLightShadowMaps={value:o,type:`tv`},b.spotLightMatrices={value:s,type:`m4v`},b.spotLightShadowMapSizes={value:T,type:`1fv`}}d.length>0&&(b.pointLightShadowMaps={value:d,type:`tv`})},renderDirectionalLightShadow:(function(){var e=new nr,t=new H,n=new Ze,r=new H,i=new H,a=new H,o=new H;return function(s,c,l,u,d,f,p){var m=this._getDepthMaterial(u),h={getMaterial:function(e){return e.shadowDepthMaterial||m},isMaterialChanged:so,getUniform:oo,ifRender:function(e){return e.castShadow},sortCompare:wn.opaqueSortCompare};if(!c.viewBoundingBoxLastFrame.isFinite()){var g=c.getBoundingBox();c.viewBoundingBoxLastFrame.copy(g).applyTransform(l.viewMatrix)}var _=Math.min(-c.viewBoundingBoxLastFrame.min.z,l.far),v=Math.max(-c.viewBoundingBoxLastFrame.max.z,l.near),y=this._getDirectionalLightCamera(u,c,l),b=a.array;o.copy(y.projectionMatrix),V.invert(i.array,y.worldTransform.array),V.multiply(i.array,i.array,l.worldTransform.array),V.multiply(b,o.array,i.array);for(var x=[],S=l instanceof _r,C=(l.near+l.far)/(l.near-l.far),w=2*l.near*l.far/(l.near-l.far),T=0;T<=u.shadowCascade;T++){var E=v*(_/v)**+(T/u.shadowCascade),D=v+(_-v)*T/u.shadowCascade,O=E*u.cascadeSplitLogFactor+D*(1-u.cascadeSplitLogFactor);x.push(O),d.push(-(-O*C+w)/-O)}var k=this._getTexture(u,u.shadowCascade);p.push(k);var A=s.viewport,j=s.gl;this._frameBuffer.attach(k),this._frameBuffer.bind(s),j.clear(j.COLOR_BUFFER_BIT|j.DEPTH_BUFFER_BIT);for(var T=0;T<u.shadowCascade;T++){var M=x[T],N=x[T+1];S?V.perspective(t.array,l.fov/180*Math.PI,l.aspect,M,N):V.ortho(t.array,l.left,l.right,l.bottom,l.top,M,N),e.setFromProjection(t),e.getTransformedBoundingBox(n,i),n.applyProjection(o);var ee=n.min.array,te=n.max.array;ee[0]=Math.max(ee[0],-1),ee[1]=Math.max(ee[1],-1),te[0]=Math.min(te[0],1),te[1]=Math.min(te[1],1),r.ortho(ee[0],te[0],ee[1],te[1],1,-1),y.projectionMatrix.multiplyLeft(r);var P=u.shadowResolution||512;s.setViewport((u.shadowCascade-T-1)*P,0,P,P,1);var ne=c.updateRenderList(y);s.renderPass(ne.opaque,y,h),this.softShadow===co.VSM&&this._gaussianFilter(s,k,k.width);var re=new H;re.copy(y.viewMatrix).multiplyLeft(y.projectionMatrix),f.push(re.array),y.projectionMatrix.copy(o)}this._frameBuffer.unbind(s),s.setViewport(A)}})(),renderSpotLightShadow:function(e,t,n,r,i){var a=this._getTexture(n),o=this._getSpotLightCamera(n),s=e.gl;this._frameBuffer.attach(a),this._frameBuffer.bind(e),s.clear(s.COLOR_BUFFER_BIT|s.DEPTH_BUFFER_BIT);var c=this._getDepthMaterial(n),l={getMaterial:function(e){return e.shadowDepthMaterial||c},isMaterialChanged:so,getUniform:oo,ifRender:function(e){return e.castShadow},sortCompare:wn.opaqueSortCompare},u=t.updateRenderList(o);e.renderPass(u.opaque,o,l),this._frameBuffer.unbind(e),this.softShadow===co.VSM&&this._gaussianFilter(e,a,a.width);var d=new H;d.copy(o.worldTransform).invert().multiplyLeft(o.projectionMatrix),i.push(a),r.push(d.array)},renderPointLightShadow:function(e,t,n,r){var i=this._getTexture(n),a=e.gl;r.push(i);var o=this._getDepthMaterial(n),s={getMaterial:function(e){return e.shadowDepthMaterial||o},getUniform:oo,sortCompare:wn.opaqueSortCompare},c={px:[],py:[],pz:[],nx:[],ny:[],nz:[]},l=new Ze,u=n.getWorldPosition().array,d=new Ze,f=n.range;d.min.setArray(u),d.max.setArray(u);var p=new L(f,f,f);d.max.add(p),d.min.sub(p);var m={px:!1,py:!1,pz:!1,nx:!1,ny:!1,nz:!1};t.traverse(function(e){if(e.isRenderable()&&e.castShadow){var t=e.geometry;if(!t.boundingBox){for(var n=0;n<ao.length;n++)c[ao[n]].push(e);return}if(l.transformFrom(t.boundingBox,e.worldTransform),!l.intersectBoundingBox(d))return;l.updateVertices();for(var n=0;n<ao.length;n++)m[ao[n]]=!1;for(var n=0;n<8;n++){var r=l.vertices[n],i=r[0]-u[0],a=r[1]-u[1],o=r[2]-u[2],s=Math.abs(i),f=Math.abs(a),p=Math.abs(o);s>f?s>p?m[i>0?`px`:`nx`]=!0:m[o>0?`pz`:`nz`]=!0:f>p?m[a>0?`py`:`ny`]=!0:m[o>0?`pz`:`nz`]=!0}for(var n=0;n<ao.length;n++)m[ao[n]]&&c[ao[n]].push(e)}});for(var h=0;h<6;h++){var g=ao[h],_=this._getPointLightCamera(n,g);this._frameBuffer.attach(i,a.COLOR_ATTACHMENT0,a.TEXTURE_CUBE_MAP_POSITIVE_X+h),this._frameBuffer.bind(e),a.clear(a.COLOR_BUFFER_BIT|a.DEPTH_BUFFER_BIT),e.renderPass(c[g],_,s)}this._frameBuffer.unbind(e)},_getDepthMaterial:function(e){var t=this._lightMaterials[e.__uid__],n=e.type===`POINT_LIGHT`;if(!t){var r=n?`clay.sm.distance.`:`clay.sm.depth.`;t=new Mt({precision:this.precision,shader:new K(K.source(r+`vertex`),K.source(r+`fragment`))}),this._lightMaterials[e.__uid__]=t}return e.shadowSlopeScale!=null&&t.setUniform(`slopeScale`,e.shadowSlopeScale),e.shadowBias!=null&&t.setUniform(`bias`,e.shadowBias),this.softShadow===co.VSM?t.define(`fragment`,`USE_VSM`):t.undefine(`fragment`,`USE_VSM`),n&&(t.set(`lightPosition`,e.getWorldPosition().array),t.set(`range`,e.range)),t},_gaussianFilter:function(e,t,n){var r={width:n,height:n,type:q.FLOAT},i=this._texturePool.get(r);this._frameBuffer.attach(i),this._frameBuffer.bind(e),this._gaussianPassH.setUniform(`texture`,t),this._gaussianPassH.setUniform(`textureWidth`,n),this._gaussianPassH.render(e),this._frameBuffer.attach(t),this._gaussianPassV.setUniform(`texture`,i),this._gaussianPassV.setUniform(`textureHeight`,n),this._gaussianPassV.render(e),this._frameBuffer.unbind(e),this._texturePool.put(i)},_getTexture:function(e,t){var n=e.__uid__,r=this._textures[n],i=e.shadowResolution||512;return t=t||1,r||(r=e.type===`POINT_LIGHT`?new hr:new J,r.width=i*t,r.height=i,this.softShadow===co.VSM?(r.type=q.FLOAT,r.anisotropic=4):(r.minFilter=U.NEAREST,r.magFilter=U.NEAREST,r.useMipmap=!1),this._textures[n]=r),r},_getPointLightCamera:function(e,t){this._lightCameras.point||(this._lightCameras.point={px:new _r,nx:new _r,py:new _r,ny:new _r,pz:new _r,nz:new _r});var n=this._lightCameras.point[t];switch(n.far=e.range,n.fov=90,n.position.set(0,0,0),t){case`px`:n.lookAt(L.POSITIVE_X,L.NEGATIVE_Y);break;case`nx`:n.lookAt(L.NEGATIVE_X,L.NEGATIVE_Y);break;case`py`:n.lookAt(L.POSITIVE_Y,L.POSITIVE_Z);break;case`ny`:n.lookAt(L.NEGATIVE_Y,L.NEGATIVE_Z);break;case`pz`:n.lookAt(L.POSITIVE_Z,L.NEGATIVE_Y);break;case`nz`:n.lookAt(L.NEGATIVE_Z,L.NEGATIVE_Y);break}return e.getWorldPosition(n.position),n.update(),n},_getDirectionalLightCamera:(function(){var e=new H,t=new Ze,n=new Ze;return function(r,i,a){this._lightCameras.directional||(this._lightCameras.directional=new _i);var o=this._lightCameras.directional;t.copy(i.viewBoundingBoxLastFrame),t.intersection(a.frustum.boundingBox),o.position.copy(t.min).add(t.max).scale(.5).transformMat4(a.worldTransform),o.rotation.copy(r.rotation),o.scale.copy(r.scale),o.updateWorldTransform(),H.invert(e,o.worldTransform),H.multiply(e,e,a.worldTransform),n.copy(t).applyTransform(e);var s=n.min.array,c=n.max.array;return o.position.set((s[0]+c[0])/2,(s[1]+c[1])/2,c[2]).transformMat4(o.worldTransform),o.near=0,o.far=-s[2]+c[2],isNaN(this.lightFrustumBias)?o.far*=4:o.far+=this.lightFrustumBias,o.left=s[0],o.right=c[0],o.top=c[1],o.bottom=s[1],o.update(!0),o}})(),_getSpotLightCamera:function(e){this._lightCameras.spot||(this._lightCameras.spot=new _r);var t=this._lightCameras.spot;return t.fov=e.penumbraAngle*2,t.far=e.range,t.worldTransform.copy(e.worldTransform),t.updateProjectionMatrix(),V.invert(t.viewMatrix.array,t.worldTransform.array),t},dispose:function(e){var t=e.gl||e;for(var n in this._frameBuffer&&this._frameBuffer.dispose(t),this._textures)this._textures[n].dispose(t);this._texturePool.clear(e.gl),this._depthMaterials={},this._distanceMaterials={},this._textures={},this._lightCameras={},this._shadowMapNumber={POINT_LIGHT:0,DIRECTIONAL_LIGHT:0,SPOT_LIGHT:0},this._meshMaterials={};for(var r=0;r<this._receivers.length;r++){var i=this._receivers[r];if(i.material){var a=i.material;a.undefine(`fragment`,`POINT_LIGHT_SHADOW_COUNT`),a.undefine(`fragment`,`DIRECTIONAL_LIGHT_SHADOW_COUNT`),a.undefine(`fragment`,`AMBIENT_LIGHT_SHADOW_COUNT`),a.set(`shadowEnabled`,0)}}this._receivers=[],this._lightsCastShadow=[]}});co.VSM=1,co.PCF=2;var lo=Fe.extend(function(){return{name:``,inputLinks:{},outputLinks:{},_prevOutputTextures:{},_outputTextures:{},_outputReferences:{},_rendering:!1,_rendered:!1,_compositor:null}},{updateParameter:function(e,t){var n=this.outputs[e],r=n.parameters,i=n._parametersCopy;if(i||(i=n._parametersCopy={}),r)for(var a in r)a!==`width`&&a!==`height`&&(i[a]=r[a]);var o=r.width instanceof Function?r.width.call(this,t):r.width,s=r.height instanceof Function?r.height.call(this,t):r.height;return(i.width!==o||i.height!==s)&&this._outputTextures[e]&&this._outputTextures[e].dispose(t.gl),i.width=o,i.height=s,i},setParameter:function(e,t){},getParameter:function(e){},setParameters:function(e){for(var t in e)this.setParameter(t,e[t])},render:function(){},getOutput:function(e,t){if(t==null)return t=e,this._outputTextures[t];var n=this.outputs[t];if(n)return this._rendered?n.outputLastFrame?this._prevOutputTextures[t]:this._outputTextures[t]:this._rendering?(this._prevOutputTextures[t]||(this._prevOutputTextures[t]=this._compositor.allocateTexture(n.parameters||{})),this._prevOutputTextures[t]):(this.render(e),this._outputTextures[t])},removeReference:function(e){this._outputReferences[e]--,this._outputReferences[e]===0&&(this.outputs[e].keepLastFrame?(this._prevOutputTextures[e]&&this._compositor.releaseTexture(this._prevOutputTextures[e]),this._prevOutputTextures[e]=this._outputTextures[e]):this._compositor.releaseTexture(this._outputTextures[e]))},link:function(e,t,n){this.inputLinks[e]={node:t,pin:n},t.outputLinks[n]||(t.outputLinks[n]=[]),t.outputLinks[n].push({node:this,pin:e}),this.pass.material.enableTexture(e)},clear:function(){this.inputLinks={},this.outputLinks={}},updateReference:function(e){if(!this._rendering){for(var t in this._rendering=!0,this.inputLinks){var n=this.inputLinks[t];n.node.updateReference(n.pin)}this._rendering=!1}e&&this._outputReferences[e]++},beforeFrame:function(){for(var e in this._rendered=!1,this.outputLinks)this._outputReferences[e]=0},afterFrame:function(){for(var e in this.outputLinks)this._outputReferences[e]>0&&(this.outputs[e].keepLastFrame?(this._prevOutputTextures[e]&&this._compositor.releaseTexture(this._prevOutputTextures[e]),this._prevOutputTextures[e]=this._outputTextures[e]):this._compositor.releaseTexture(this._outputTextures[e]))}}),uo=Fe.extend(function(){return{nodes:[]}},{dirty:function(){this._dirty=!0},addNode:function(e){this.nodes.indexOf(e)>=0||(this.nodes.push(e),this._dirty=!0)},removeNode:function(e){typeof e==`string`&&(e=this.getNodeByName(e));var t=this.nodes.indexOf(e);t>=0&&(this.nodes.splice(t,1),this._dirty=!0)},getNodeByName:function(e){for(var t=0;t<this.nodes.length;t++)if(this.nodes[t].name===e)return this.nodes[t]},update:function(){for(var e=0;e<this.nodes.length;e++)this.nodes[e].clear();for(var e=0;e<this.nodes.length;e++){var t=this.nodes[e];if(t.inputs){for(var n in t.inputs)if(t.inputs[n]){if(t.pass&&!t.pass.material.isUniformEnabled(n)){console.warn(`Pin `+t.name+`.`+n+` not used.`);continue}var r=t.inputs[n],i=this.findPin(r);i?t.link(n,i.node,i.pin):console.warn(typeof r==`string`?`Node `+r+` not exist`:`Pin of `+r.node+`.`+r.pin+` not exist`)}}}},findPin:function(e){var t;if((typeof e==`string`||e instanceof lo)&&(e={node:e}),typeof e.node==`string`)for(var n=0;n<this.nodes.length;n++){var r=this.nodes[n];r.name===e.node&&(t=r)}else t=e.node;if(t){var i=e.pin;if(i||t.outputs&&(i=Object.keys(t.outputs)[0]),t.outputs[i])return{node:t,pin:i}}}}),fo=uo.extend(function(){return{_outputs:[],_texturePool:new Qa,_frameBuffer:new Or({depthBuffer:!1})}},{addNode:function(e){uo.prototype.addNode.call(this,e),e._compositor=this},render:function(e,t){if(this._dirty){this.update(),this._dirty=!1,this._outputs.length=0;for(var n=0;n<this.nodes.length;n++)this.nodes[n].outputs||this._outputs.push(this.nodes[n])}for(var n=0;n<this.nodes.length;n++)this.nodes[n].beforeFrame();for(var n=0;n<this._outputs.length;n++)this._outputs[n].updateReference();for(var n=0;n<this._outputs.length;n++)this._outputs[n].render(e,t);for(var n=0;n<this.nodes.length;n++)this.nodes[n].afterFrame()},allocateTexture:function(e){return this._texturePool.get(e)},releaseTexture:function(e){this._texturePool.put(e)},getFrameBuffer:function(){return this._frameBuffer},dispose:function(e){this._texturePool.clear(e)}}),po=lo.extend({name:`scene`,scene:null,camera:null,autoUpdateScene:!0,preZ:!1},function(){this.frameBuffer=new Or},{render:function(e){this._rendering=!0;var t=e.gl;this.trigger(`beforerender`);var n;if(!this.outputs)n=e.render(this.scene,this.camera,!this.autoUpdateScene,this.preZ);else{var r=this.frameBuffer;for(var i in this.outputs){var a=this.updateParameter(i,e),o=this.outputs[i],s=this._compositor.allocateTexture(a);this._outputTextures[i]=s;var c=o.attachment||t.COLOR_ATTACHMENT0;typeof c==`string`&&(c=t[c]),r.attach(s,c)}r.bind(e);var l=e.getGLExtension(`EXT_draw_buffers`);if(l){var u=[];for(var c in this.outputs)c=parseInt(c),c>=t.COLOR_ATTACHMENT0&&c<=t.COLOR_ATTACHMENT0+8&&u.push(c);l.drawBuffersEXT(u)}e.saveClear(),e.clearBit=U.DEPTH_BUFFER_BIT|U.COLOR_BUFFER_BIT,n=e.render(this.scene,this.camera,!this.autoUpdateScene,this.preZ),e.restoreClear(),r.unbind(e)}this.trigger(`afterrender`,n),this._rendering=!1,this._rendered=!0}}),mo=lo.extend(function(){return{texture:null,outputs:{color:{}}}},function(){},{getOutput:function(e,t){return this.texture},beforeFrame:function(){},afterFrame:function(){}}),ho=lo.extend(function(){return{name:``,inputs:{},outputs:null,shader:``,inputLinks:{},outputLinks:{},pass:null,_prevOutputTextures:{},_outputTextures:{},_outputReferences:{},_rendering:!1,_rendered:!1,_compositor:null}},function(){var e=new bi({fragment:this.shader});this.pass=e},{render:function(e,t){this.trigger(`beforerender`,e),this._rendering=!0;var n=e.gl;for(var r in this.inputLinks){var i=this.inputLinks[r],a=i.node.getOutput(e,i.pin);this.pass.setUniform(r,a)}if(!this.outputs)this.pass.outputs=null,this._compositor.getFrameBuffer().unbind(e),this.pass.render(e,t);else{this.pass.outputs={};var o={};for(var s in this.outputs){var c=this.updateParameter(s,e);isNaN(c.width)&&this.updateParameter(s,e);var l=this.outputs[s],u=this._compositor.allocateTexture(c);this._outputTextures[s]=u;var d=l.attachment||n.COLOR_ATTACHMENT0;typeof d==`string`&&(d=n[d]),o[d]=u}for(var d in this._compositor.getFrameBuffer().bind(e),o)this._compositor.getFrameBuffer().attach(o[d],d);this.pass.render(e),this._compositor.getFrameBuffer().updateMipmap(e)}for(var r in this.inputLinks){var i=this.inputLinks[r];i.node.removeReference(i.pin)}this._rendering=!1,this._rendered=!0,this.trigger(`afterrender`,e)},updateParameter:function(e,t){var n=this.outputs[e],r=n.parameters,i=n._parametersCopy;if(i||(i=n._parametersCopy={}),r)for(var a in r)a!==`width`&&a!==`height`&&(i[a]=r[a]);var o=typeof r.width==`function`?r.width.call(this,t):r.width,s=typeof r.height==`function`?r.height.call(this,t):r.height;return o=Math.ceil(o),s=Math.ceil(s),(i.width!==o||i.height!==s)&&this._outputTextures[e]&&this._outputTextures[e].dispose(t),i.width=o,i.height=s,i},setParameter:function(e,t){this.pass.setUniform(e,t)},getParameter:function(e){return this.pass.getUniform(e)},setParameters:function(e){for(var t in e)this.setParameter(t,e[t])},define:function(e,t){this.pass.material.define(`fragment`,e,t)},undefine:function(e){this.pass.material.undefine(`fragment`,e)},removeReference:function(e){this._outputReferences[e]--,this._outputReferences[e]===0&&(this.outputs[e].keepLastFrame?(this._prevOutputTextures[e]&&this._compositor.releaseTexture(this._prevOutputTextures[e]),this._prevOutputTextures[e]=this._outputTextures[e]):this._compositor.releaseTexture(this._outputTextures[e]))},clear:function(){lo.prototype.clear.call(this),this.pass.material.disableTexturesAll()}}),go=`@export clay.compositor.coloradjust
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float brightness : 0.0;
uniform float contrast : 1.0;
uniform float exposure : 0.0;
uniform float gamma : 1.0;
uniform float saturation : 1.0;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord);
 vec3 color = clamp(tex.rgb + vec3(brightness), 0.0, 1.0);
 color = clamp( (color-vec3(0.5))*contrast+vec3(0.5), 0.0, 1.0);
 color = clamp( color * pow(2.0, exposure), 0.0, 1.0);
 color = clamp( pow(color, vec3(gamma)), 0.0, 1.0);
 float luminance = dot( color, w );
 color = mix(vec3(luminance), color, saturation);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.brightness
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float brightness : 0.0;
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord);
 vec3 color = tex.rgb + vec3(brightness);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.contrast
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float contrast : 1.0;
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord);
 vec3 color = (tex.rgb-vec3(0.5))*contrast+vec3(0.5);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.exposure
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float exposure : 0.0;
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 vec3 color = tex.rgb * pow(2.0, exposure);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.gamma
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float gamma : 1.0;
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 vec3 color = pow(tex.rgb, vec3(gamma));
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.saturation
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float saturation : 1.0;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 vec3 color = tex.rgb;
 float luminance = dot(color, w);
 color = mix(vec3(luminance), color, saturation);
 gl_FragColor = vec4(color, tex.a);
}
@end`,_o=`@export clay.compositor.kernel.gaussian_9
float gaussianKernel[9];
gaussianKernel[0] = 0.07;
gaussianKernel[1] = 0.09;
gaussianKernel[2] = 0.12;
gaussianKernel[3] = 0.14;
gaussianKernel[4] = 0.16;
gaussianKernel[5] = 0.14;
gaussianKernel[6] = 0.12;
gaussianKernel[7] = 0.09;
gaussianKernel[8] = 0.07;
@end
@export clay.compositor.kernel.gaussian_13
float gaussianKernel[13];
gaussianKernel[0] = 0.02;
gaussianKernel[1] = 0.03;
gaussianKernel[2] = 0.06;
gaussianKernel[3] = 0.08;
gaussianKernel[4] = 0.11;
gaussianKernel[5] = 0.13;
gaussianKernel[6] = 0.14;
gaussianKernel[7] = 0.13;
gaussianKernel[8] = 0.11;
gaussianKernel[9] = 0.08;
gaussianKernel[10] = 0.06;
gaussianKernel[11] = 0.03;
gaussianKernel[12] = 0.02;
@end
@export clay.compositor.gaussian_blur
#define SHADER_NAME gaussian_blur
uniform sampler2D texture;varying vec2 v_Texcoord;
uniform float blurSize : 2.0;
uniform vec2 textureSize : [512.0, 512.0];
uniform float blurDir : 0.0;
@import clay.util.rgbm
@import clay.util.clamp_sample
void main (void)
{
 @import clay.compositor.kernel.gaussian_9
 vec2 off = blurSize / textureSize;
 off *= vec2(1.0 - blurDir, blurDir);
 vec4 sum = vec4(0.0);
 float weightAll = 0.0;
 for (int i = 0; i < 9; i++) {
 float w = gaussianKernel[i];
 vec4 texel = decodeHDR(clampSample(texture, v_Texcoord + float(i - 4) * off));
 sum += texel * w;
 weightAll += w;
 }
 gl_FragColor = encodeHDR(sum / max(weightAll, 0.01));
}
@end
`,vo=`@export clay.compositor.hdr.log_lum
varying vec2 v_Texcoord;
uniform sampler2D texture;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
@import clay.util.rgbm
void main()
{
 vec4 tex = decodeHDR(texture2D(texture, v_Texcoord));
 float luminance = dot(tex.rgb, w);
 luminance = log(luminance + 0.001);
 gl_FragColor = encodeHDR(vec4(vec3(luminance), 1.0));
}
@end
@export clay.compositor.hdr.lum_adaption
varying vec2 v_Texcoord;
uniform sampler2D adaptedLum;
uniform sampler2D currentLum;
uniform float frameTime : 0.02;
@import clay.util.rgbm
void main()
{
 float fAdaptedLum = decodeHDR(texture2D(adaptedLum, vec2(0.5, 0.5))).r;
 float fCurrentLum = exp(encodeHDR(texture2D(currentLum, vec2(0.5, 0.5))).r);
 fAdaptedLum += (fCurrentLum - fAdaptedLum) * (1.0 - pow(0.98, 30.0 * frameTime));
 gl_FragColor = encodeHDR(vec4(vec3(fAdaptedLum), 1.0));
}
@end
@export clay.compositor.lum
varying vec2 v_Texcoord;
uniform sampler2D texture;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord );
 float luminance = dot(tex.rgb, w);
 gl_FragColor = vec4(vec3(luminance), 1.0);
}
@end`,yo=`
@export clay.compositor.lut
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform sampler2D lookup;
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 float blueColor = tex.b * 63.0;
 vec2 quad1;
 quad1.y = floor(floor(blueColor) / 8.0);
 quad1.x = floor(blueColor) - (quad1.y * 8.0);
 vec2 quad2;
 quad2.y = floor(ceil(blueColor) / 8.0);
 quad2.x = ceil(blueColor) - (quad2.y * 8.0);
 vec2 texPos1;
 texPos1.x = (quad1.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.r);
 texPos1.y = (quad1.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.g);
 vec2 texPos2;
 texPos2.x = (quad2.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.r);
 texPos2.y = (quad2.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.g);
 vec4 newColor1 = texture2D(lookup, texPos1);
 vec4 newColor2 = texture2D(lookup, texPos2);
 vec4 newColor = mix(newColor1, newColor2, fract(blueColor));
 gl_FragColor = vec4(newColor.rgb, tex.w);
}
@end`,bo=`@export clay.compositor.vignette
#define OUTPUT_ALPHA
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float darkness: 1;
uniform float offset: 1;
@import clay.util.rgbm
void main()
{
 vec4 texel = decodeHDR(texture2D(texture, v_Texcoord));
 gl_FragColor.rgb = texel.rgb;
 vec2 uv = (v_Texcoord - vec2(0.5)) * vec2(offset);
 gl_FragColor = encodeHDR(vec4(mix(texel.rgb, vec3(1.0 - darkness), dot(uv, uv)), texel.a));
}
@end`,xo=`@export clay.compositor.output
#define OUTPUT_ALPHA
varying vec2 v_Texcoord;
uniform sampler2D texture;
@import clay.util.rgbm
void main()
{
 vec4 tex = decodeHDR(texture2D(texture, v_Texcoord));
 gl_FragColor.rgb = tex.rgb;
#ifdef OUTPUT_ALPHA
 gl_FragColor.a = tex.a;
#else
 gl_FragColor.a = 1.0;
#endif
 gl_FragColor = encodeHDR(gl_FragColor);
#ifdef PREMULTIPLY_ALPHA
 gl_FragColor.rgb *= gl_FragColor.a;
#endif
}
@end`,So=`@export clay.compositor.bright
uniform sampler2D texture;
uniform float threshold : 1;
uniform float scale : 1.0;
uniform vec2 textureSize: [512, 512];
varying vec2 v_Texcoord;
const vec3 lumWeight = vec3(0.2125, 0.7154, 0.0721);
@import clay.util.rgbm
vec4 median(vec4 a, vec4 b, vec4 c)
{
 return a + b + c - min(min(a, b), c) - max(max(a, b), c);
}
void main()
{
 vec4 texel = decodeHDR(texture2D(texture, v_Texcoord));
#ifdef ANTI_FLICKER
 vec3 d = 1.0 / textureSize.xyx * vec3(1.0, 1.0, 0.0);
 vec4 s1 = decodeHDR(texture2D(texture, v_Texcoord - d.xz));
 vec4 s2 = decodeHDR(texture2D(texture, v_Texcoord + d.xz));
 vec4 s3 = decodeHDR(texture2D(texture, v_Texcoord - d.zy));
 vec4 s4 = decodeHDR(texture2D(texture, v_Texcoord + d.zy));
 texel = median(median(texel, s1, s2), s3, s4);
#endif
 float lum = dot(texel.rgb , lumWeight);
 vec4 color;
 if (lum > threshold && texel.a > 0.0)
 {
 color = vec4(texel.rgb * scale, texel.a * scale);
 }
 else
 {
 color = vec4(0.0);
 }
 gl_FragColor = encodeHDR(color);
}
@end
`,Co=`@export clay.compositor.downsample
uniform sampler2D texture;
uniform vec2 textureSize : [512, 512];
varying vec2 v_Texcoord;
@import clay.util.rgbm
float brightness(vec3 c)
{
 return max(max(c.r, c.g), c.b);
}
@import clay.util.clamp_sample
void main()
{
 vec4 d = vec4(-1.0, -1.0, 1.0, 1.0) / textureSize.xyxy;
#ifdef ANTI_FLICKER
 vec3 s1 = decodeHDR(clampSample(texture, v_Texcoord + d.xy)).rgb;
 vec3 s2 = decodeHDR(clampSample(texture, v_Texcoord + d.zy)).rgb;
 vec3 s3 = decodeHDR(clampSample(texture, v_Texcoord + d.xw)).rgb;
 vec3 s4 = decodeHDR(clampSample(texture, v_Texcoord + d.zw)).rgb;
 float s1w = 1.0 / (brightness(s1) + 1.0);
 float s2w = 1.0 / (brightness(s2) + 1.0);
 float s3w = 1.0 / (brightness(s3) + 1.0);
 float s4w = 1.0 / (brightness(s4) + 1.0);
 float oneDivideSum = 1.0 / (s1w + s2w + s3w + s4w);
 vec4 color = vec4(
 (s1 * s1w + s2 * s2w + s3 * s3w + s4 * s4w) * oneDivideSum,
 1.0
 );
#else
 vec4 color = decodeHDR(clampSample(texture, v_Texcoord + d.xy));
 color += decodeHDR(clampSample(texture, v_Texcoord + d.zy));
 color += decodeHDR(clampSample(texture, v_Texcoord + d.xw));
 color += decodeHDR(clampSample(texture, v_Texcoord + d.zw));
 color *= 0.25;
#endif
 gl_FragColor = encodeHDR(color);
}
@end`,wo=`
@export clay.compositor.upsample
#define HIGH_QUALITY
uniform sampler2D texture;
uniform vec2 textureSize : [512, 512];
uniform float sampleScale: 0.5;
varying vec2 v_Texcoord;
@import clay.util.rgbm
@import clay.util.clamp_sample
void main()
{
#ifdef HIGH_QUALITY
 vec4 d = vec4(1.0, 1.0, -1.0, 0.0) / textureSize.xyxy * sampleScale;
 vec4 s;
 s = decodeHDR(clampSample(texture, v_Texcoord - d.xy));
 s += decodeHDR(clampSample(texture, v_Texcoord - d.wy)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord - d.zy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zw)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord )) * 4.0;
 s += decodeHDR(clampSample(texture, v_Texcoord + d.xw)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.wy)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord + d.xy));
 gl_FragColor = encodeHDR(s / 16.0);
#else
 vec4 d = vec4(-1.0, -1.0, +1.0, +1.0) / textureSize.xyxy;
 vec4 s;
 s = decodeHDR(clampSample(texture, v_Texcoord + d.xy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.xw));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zw));
 gl_FragColor = encodeHDR(s / 4.0);
#endif
}
@end`,To=`@export clay.compositor.hdr.composite
#define TONEMAPPING
uniform sampler2D texture;
#ifdef BLOOM_ENABLED
uniform sampler2D bloom;
#endif
#ifdef LENSFLARE_ENABLED
uniform sampler2D lensflare;
uniform sampler2D lensdirt;
#endif
#ifdef LUM_ENABLED
uniform sampler2D lum;
#endif
#ifdef LUT_ENABLED
uniform sampler2D lut;
#endif
#ifdef COLOR_CORRECTION
uniform float brightness : 0.0;
uniform float contrast : 1.0;
uniform float saturation : 1.0;
#endif
#ifdef VIGNETTE
uniform float vignetteDarkness: 1.0;
uniform float vignetteOffset: 1.0;
#endif
uniform float exposure : 1.0;
uniform float bloomIntensity : 0.25;
uniform float lensflareIntensity : 1;
varying vec2 v_Texcoord;
@import clay.util.srgb
vec3 ACESToneMapping(vec3 color)
{
 const float A = 2.51;
 const float B = 0.03;
 const float C = 2.43;
 const float D = 0.59;
 const float E = 0.14;
 return (color * (A * color + B)) / (color * (C * color + D) + E);
}
float eyeAdaption(float fLum)
{
 return mix(0.2, fLum, 0.5);
}
#ifdef LUT_ENABLED
vec3 lutTransform(vec3 color) {
 float blueColor = color.b * 63.0;
 vec2 quad1;
 quad1.y = floor(floor(blueColor) / 8.0);
 quad1.x = floor(blueColor) - (quad1.y * 8.0);
 vec2 quad2;
 quad2.y = floor(ceil(blueColor) / 8.0);
 quad2.x = ceil(blueColor) - (quad2.y * 8.0);
 vec2 texPos1;
 texPos1.x = (quad1.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.r);
 texPos1.y = (quad1.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.g);
 vec2 texPos2;
 texPos2.x = (quad2.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.r);
 texPos2.y = (quad2.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.g);
 vec4 newColor1 = texture2D(lut, texPos1);
 vec4 newColor2 = texture2D(lut, texPos2);
 vec4 newColor = mix(newColor1, newColor2, fract(blueColor));
 return newColor.rgb;
}
#endif
@import clay.util.rgbm
void main()
{
 vec4 texel = vec4(0.0);
 vec4 originalTexel = vec4(0.0);
#ifdef TEXTURE_ENABLED
 texel = decodeHDR(texture2D(texture, v_Texcoord));
 originalTexel = texel;
#endif
#ifdef BLOOM_ENABLED
 vec4 bloomTexel = decodeHDR(texture2D(bloom, v_Texcoord));
 texel.rgb += bloomTexel.rgb * bloomIntensity;
 texel.a += bloomTexel.a * bloomIntensity;
#endif
#ifdef LENSFLARE_ENABLED
 texel += decodeHDR(texture2D(lensflare, v_Texcoord)) * texture2D(lensdirt, v_Texcoord) * lensflareIntensity;
#endif
 texel.a = min(texel.a, 1.0);
#ifdef LUM_ENABLED
 float fLum = texture2D(lum, vec2(0.5, 0.5)).r;
 float adaptedLumDest = 3.0 / (max(0.1, 1.0 + 10.0*eyeAdaption(fLum)));
 float exposureBias = adaptedLumDest * exposure;
#else
 float exposureBias = exposure;
#endif
#ifdef TONEMAPPING
 texel.rgb *= exposureBias;
 texel.rgb = ACESToneMapping(texel.rgb);
#endif
 texel = linearTosRGB(texel);
#ifdef LUT_ENABLED
 texel.rgb = lutTransform(clamp(texel.rgb,vec3(0.0),vec3(1.0)));
#endif
#ifdef COLOR_CORRECTION
 texel.rgb = clamp(texel.rgb + vec3(brightness), 0.0, 1.0);
 texel.rgb = clamp((texel.rgb - vec3(0.5))*contrast+vec3(0.5), 0.0, 1.0);
 float lum = dot(texel.rgb, vec3(0.2125, 0.7154, 0.0721));
 texel.rgb = mix(vec3(lum), texel.rgb, saturation);
#endif
#ifdef VIGNETTE
 vec2 uv = (v_Texcoord - vec2(0.5)) * vec2(vignetteOffset);
 texel.rgb = mix(texel.rgb, vec3(1.0 - vignetteDarkness), dot(uv, uv));
#endif
 gl_FragColor = encodeHDR(texel);
#ifdef DEBUG
 #if DEBUG == 1
 gl_FragColor = encodeHDR(decodeHDR(texture2D(texture, v_Texcoord)));
 #elif DEBUG == 2
 gl_FragColor = encodeHDR(decodeHDR(texture2D(bloom, v_Texcoord)) * bloomIntensity);
 #elif DEBUG == 3
 gl_FragColor = encodeHDR(decodeHDR(texture2D(lensflare, v_Texcoord) * lensflareIntensity));
 #endif
#endif
 if (originalTexel.a <= 0.01 && gl_FragColor.a > 1e-5) {
 gl_FragColor.a = dot(gl_FragColor.rgb, vec3(0.2125, 0.7154, 0.0721));
 }
#ifdef PREMULTIPLY_ALPHA
 gl_FragColor.rgb *= gl_FragColor.a;
#endif
}
@end`,Eo=`@export clay.compositor.lensflare
#define SAMPLE_NUMBER 8
uniform sampler2D texture;
uniform sampler2D lenscolor;
uniform vec2 textureSize : [512, 512];
uniform float dispersal : 0.3;
uniform float haloWidth : 0.4;
uniform float distortion : 1.0;
varying vec2 v_Texcoord;
@import clay.util.rgbm
vec4 textureDistorted(
 in vec2 texcoord,
 in vec2 direction,
 in vec3 distortion
) {
 return vec4(
 decodeHDR(texture2D(texture, texcoord + direction * distortion.r)).r,
 decodeHDR(texture2D(texture, texcoord + direction * distortion.g)).g,
 decodeHDR(texture2D(texture, texcoord + direction * distortion.b)).b,
 1.0
 );
}
void main()
{
 vec2 texcoord = -v_Texcoord + vec2(1.0); vec2 textureOffset = 1.0 / textureSize;
 vec2 ghostVec = (vec2(0.5) - texcoord) * dispersal;
 vec2 haloVec = normalize(ghostVec) * haloWidth;
 vec3 distortion = vec3(-textureOffset.x * distortion, 0.0, textureOffset.x * distortion);
 vec4 result = vec4(0.0);
 for (int i = 0; i < SAMPLE_NUMBER; i++)
 {
 vec2 offset = fract(texcoord + ghostVec * float(i));
 float weight = length(vec2(0.5) - offset) / length(vec2(0.5));
 weight = pow(1.0 - weight, 10.0);
 result += textureDistorted(offset, normalize(ghostVec), distortion) * weight;
 }
 result *= texture2D(lenscolor, vec2(length(vec2(0.5) - texcoord)) / length(vec2(0.5)));
 float weight = length(vec2(0.5) - fract(texcoord + haloVec)) / length(vec2(0.5));
 weight = pow(1.0 - weight, 10.0);
 vec2 offset = fract(texcoord + haloVec);
 result += textureDistorted(offset, normalize(ghostVec), distortion) * weight;
 gl_FragColor = result;
}
@end`,Do=`@export clay.compositor.blend
#define SHADER_NAME blend
#ifdef TEXTURE1_ENABLED
uniform sampler2D texture1;
uniform float weight1 : 1.0;
#endif
#ifdef TEXTURE2_ENABLED
uniform sampler2D texture2;
uniform float weight2 : 1.0;
#endif
#ifdef TEXTURE3_ENABLED
uniform sampler2D texture3;
uniform float weight3 : 1.0;
#endif
#ifdef TEXTURE4_ENABLED
uniform sampler2D texture4;
uniform float weight4 : 1.0;
#endif
#ifdef TEXTURE5_ENABLED
uniform sampler2D texture5;
uniform float weight5 : 1.0;
#endif
#ifdef TEXTURE6_ENABLED
uniform sampler2D texture6;
uniform float weight6 : 1.0;
#endif
varying vec2 v_Texcoord;
@import clay.util.rgbm
void main()
{
 vec4 tex = vec4(0.0);
#ifdef TEXTURE1_ENABLED
 tex += decodeHDR(texture2D(texture1, v_Texcoord)) * weight1;
#endif
#ifdef TEXTURE2_ENABLED
 tex += decodeHDR(texture2D(texture2, v_Texcoord)) * weight2;
#endif
#ifdef TEXTURE3_ENABLED
 tex += decodeHDR(texture2D(texture3, v_Texcoord)) * weight3;
#endif
#ifdef TEXTURE4_ENABLED
 tex += decodeHDR(texture2D(texture4, v_Texcoord)) * weight4;
#endif
#ifdef TEXTURE5_ENABLED
 tex += decodeHDR(texture2D(texture5, v_Texcoord)) * weight5;
#endif
#ifdef TEXTURE6_ENABLED
 tex += decodeHDR(texture2D(texture6, v_Texcoord)) * weight6;
#endif
 gl_FragColor = encodeHDR(tex);
}
@end`,Oo=`@export clay.compositor.fxaa
uniform sampler2D texture;
uniform vec4 viewport : VIEWPORT;
varying vec2 v_Texcoord;
#define FXAA_REDUCE_MIN (1.0/128.0)
#define FXAA_REDUCE_MUL (1.0/8.0)
#define FXAA_SPAN_MAX 8.0
@import clay.util.rgbm
void main()
{
 vec2 resolution = 1.0 / viewport.zw;
 vec3 rgbNW = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( -1.0, -1.0 ) ) * resolution ) ).xyz;
 vec3 rgbNE = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( 1.0, -1.0 ) ) * resolution ) ).xyz;
 vec3 rgbSW = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( -1.0, 1.0 ) ) * resolution ) ).xyz;
 vec3 rgbSE = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( 1.0, 1.0 ) ) * resolution ) ).xyz;
 vec4 rgbaM = decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution ) );
 vec3 rgbM = rgbaM.xyz;
 float opacity = rgbaM.w;
 vec3 luma = vec3( 0.299, 0.587, 0.114 );
 float lumaNW = dot( rgbNW, luma );
 float lumaNE = dot( rgbNE, luma );
 float lumaSW = dot( rgbSW, luma );
 float lumaSE = dot( rgbSE, luma );
 float lumaM = dot( rgbM, luma );
 float lumaMin = min( lumaM, min( min( lumaNW, lumaNE ), min( lumaSW, lumaSE ) ) );
 float lumaMax = max( lumaM, max( max( lumaNW, lumaNE) , max( lumaSW, lumaSE ) ) );
 vec2 dir;
 dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
 dir.y = ((lumaNW + lumaSW) - (lumaNE + lumaSE));
 float dirReduce = max( ( lumaNW + lumaNE + lumaSW + lumaSE ) * ( 0.25 * FXAA_REDUCE_MUL ), FXAA_REDUCE_MIN );
 float rcpDirMin = 1.0 / ( min( abs( dir.x ), abs( dir.y ) ) + dirReduce );
 dir = min( vec2( FXAA_SPAN_MAX, FXAA_SPAN_MAX),
 max( vec2(-FXAA_SPAN_MAX, -FXAA_SPAN_MAX),
 dir * rcpDirMin)) * resolution;
 vec3 rgbA = decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * ( 1.0 / 3.0 - 0.5 ) ) ).xyz;
 rgbA += decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * ( 2.0 / 3.0 - 0.5 ) ) ).xyz;
 rgbA *= 0.5;
 vec3 rgbB = decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * -0.5 ) ).xyz;
 rgbB += decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * 0.5 ) ).xyz;
 rgbB *= 0.25;
 rgbB += rgbA * 0.5;
 float lumaB = dot( rgbB, luma );
 if ( ( lumaB < lumaMin ) || ( lumaB > lumaMax ) )
 {
 gl_FragColor = vec4( rgbA, opacity );
 }
 else {
 gl_FragColor = vec4( rgbB, opacity );
 }
}
@end`;function ko(e){e.import(go),e.import(_o),e.import(vo),e.import(yo),e.import(bo),e.import(xo),e.import(So),e.import(Co),e.import(wo),e.import(To),e.import(Eo),e.import(Do),e.import(Oo)}ko(K);var Ao=/^#source\((.*?)\)/;function jo(e,t){var n=new fo;t=t||{};var r={textures:{},parameters:{}},i=function(i,a){for(var o=0;o<e.nodes.length;o++){var s=e.nodes[o],c=Mo(s,r,t);c&&n.addNode(c)}};for(var a in e.parameters){var o=e.parameters[a];r.parameters[a]=Fo(o)}return Io(e,r,t,function(e){r.textures=e,i()}),n}function Mo(e,t,n){var r=e.type||`filter`,i,a,o;if(r===`filter`){var s=e.shader.trim(),c=Ao.exec(s);if(c?i=K.source(c[1].trim()):s.charAt(0)===`#`&&(i=t.shaders[s.substr(1)]),i||(i=s),!i)return}if(e.inputs)for(var l in a={},e.inputs)typeof e.inputs[l]==`string`?a[l]=e.inputs[l]:a[l]={node:e.inputs[l].node,pin:e.inputs[l].pin};if(e.outputs)for(var l in o={},e.outputs){var u=e.outputs[l];o[l]={},u.attachment!=null&&(o[l].attachment=u.attachment),u.keepLastFrame!=null&&(o[l].keepLastFrame=u.keepLastFrame),u.outputLastFrame!=null&&(o[l].outputLastFrame=u.outputLastFrame),u.parameters&&(o[l].parameters=Fo(u.parameters))}var d=r===`scene`?new po({name:e.name,scene:n.scene,camera:n.camera,outputs:o}):r===`texture`?new mo({name:e.name,outputs:o}):new ho({name:e.name,shader:i,inputs:a,outputs:o});if(d){if(e.parameters)for(var l in e.parameters){var f=e.parameters[l];typeof f==`string`?(f=f.trim(),f.charAt(0)===`#`?f=t.textures[f.substr(1)]:d.on(`beforerender`,Lo(l,zo(f)))):typeof f==`function`&&d.on(`beforerender`,f),d.setParameter(l,f)}if(e.defines&&d.pass)for(var l in e.defines){var f=e.defines[l];d.pass.material.define(`fragment`,l,f)}}return d}function No(e,t){return e}function Po(e,t){return t}function Fo(e){var t={};if(!e)return t;[`type`,`minFilter`,`magFilter`,`wrapS`,`wrapT`,`flipY`,`useMipmap`].forEach(function(n){var r=e[n];r!=null&&(typeof r==`string`&&(r=q[r]),t[n]=r)});var n=e.scale||1;return[`width`,`height`].forEach(function(r){if(e[r]!=null){var i=e[r];typeof i==`string`?(i=i.trim(),t[r]=Ro(r,zo(i),n)):t[r]=i}}),t.width||(t.width=No),t.height||(t.height=Po),e.useMipmap!=null&&(t.useMipmap=e.useMipmap),t}function Io(e,t,n,r){if(!e.textures){r({});return}var i={},a=0,o=!1,s=n.textureRootPath;Pe.each(e.textures,function(e,t){var n,c=e.path,l=Fo(e.parameters);if(Array.isArray(c)&&c.length===6)s&&(c=c.map(function(e){return Pe.relative2absolute(e,s)})),n=new hr(l);else if(typeof c==`string`)s&&(c=Pe.relative2absolute(c,s)),n=new J(l);else return;n.load(c),a++,n.once(`success`,function(){i[t]=n,a--,a===0&&(r(i),o=!0)})}),a===0&&!o&&r(i)}function Lo(e,t){return function(n){var r=n.getDevicePixelRatio(),i=t(n.getWidth(),n.getHeight(),r);this.setParameter(e,i)}}function Ro(e,t,n){return n=n||1,function(e){var r=e.getDevicePixelRatio();return t(e.getWidth()*n,e.getHeight()*n,r)}}function zo(e){var t=/^expr\((.*)\)$/.exec(e);if(t)try{var n=Function(`width`,`height`,`dpr`,`return `+t[1]);return n(1,1),n}catch(e){throw Error(`Invalid expression.`)}}var Bo=jo;function Vo(e,t){for(var n=0,r=1/t,i=e;i>0;)n+=i%t*r,i=Math.floor(i/t),r/=t;return n}K.import(`@export ecgl.ssao.estimate

uniform sampler2D depthTex;

uniform sampler2D normalTex;

uniform sampler2D noiseTex;

uniform vec2 depthTexSize;

uniform vec2 noiseTexSize;

uniform mat4 projection;

uniform mat4 projectionInv;

uniform mat4 viewInverseTranspose;

uniform vec3 kernel[KERNEL_SIZE];

uniform float radius : 1;

uniform float power : 1;

uniform float bias: 1e-2;

uniform float intensity: 1.0;

varying vec2 v_Texcoord;

float ssaoEstimator(in vec3 originPos, in mat3 kernelBasis) {
 float occlusion = 0.0;

 for (int i = 0; i < KERNEL_SIZE; i++) {
 vec3 samplePos = kernel[i];
#ifdef NORMALTEX_ENABLED
 samplePos = kernelBasis * samplePos;
#endif
 samplePos = samplePos * radius + originPos;

 vec4 texCoord = projection * vec4(samplePos, 1.0);
 texCoord.xy /= texCoord.w;

 vec4 depthTexel = texture2D(depthTex, texCoord.xy * 0.5 + 0.5);

 float sampleDepth = depthTexel.r * 2.0 - 1.0;
 if (projection[3][3] == 0.0) {
 sampleDepth = projection[3][2] / (sampleDepth * projection[2][3] - projection[2][2]);
 }
 else {
 sampleDepth = (sampleDepth - projection[3][2]) / projection[2][2];
 }
 
 float rangeCheck = smoothstep(0.0, 1.0, radius / abs(originPos.z - sampleDepth));
 occlusion += rangeCheck * step(samplePos.z, sampleDepth - bias);
 }
#ifdef NORMALTEX_ENABLED
 occlusion = 1.0 - occlusion / float(KERNEL_SIZE);
#else
 occlusion = 1.0 - clamp((occlusion / float(KERNEL_SIZE) - 0.6) * 2.5, 0.0, 1.0);
#endif
 return pow(occlusion, power);
}

void main()
{

 vec4 depthTexel = texture2D(depthTex, v_Texcoord);

#ifdef NORMALTEX_ENABLED
 vec4 tex = texture2D(normalTex, v_Texcoord);
 if (dot(tex.rgb, tex.rgb) == 0.0) {
 gl_FragColor = vec4(1.0);
 return;
 }
 vec3 N = tex.rgb * 2.0 - 1.0;
 N = (viewInverseTranspose * vec4(N, 0.0)).xyz;

 vec2 noiseTexCoord = depthTexSize / vec2(noiseTexSize) * v_Texcoord;
 vec3 rvec = texture2D(noiseTex, noiseTexCoord).rgb * 2.0 - 1.0;
 vec3 T = normalize(rvec - N * dot(rvec, N));
 vec3 BT = normalize(cross(N, T));
 mat3 kernelBasis = mat3(T, BT, N);
#else
 if (depthTexel.r > 0.99999) {
 gl_FragColor = vec4(1.0);
 return;
 }
 mat3 kernelBasis;
#endif

 float z = depthTexel.r * 2.0 - 1.0;

 vec4 projectedPos = vec4(v_Texcoord * 2.0 - 1.0, z, 1.0);
 vec4 p4 = projectionInv * projectedPos;

 vec3 position = p4.xyz / p4.w;

 float ao = ssaoEstimator(position, kernelBasis);
 ao = clamp(1.0 - (1.0 - ao) * intensity, 0.0, 1.0);
 gl_FragColor = vec4(vec3(ao), 1.0);
}

@end


@export ecgl.ssao.blur
#define SHADER_NAME SSAO_BLUR

uniform sampler2D ssaoTexture;

#ifdef NORMALTEX_ENABLED
uniform sampler2D normalTex;
#endif

varying vec2 v_Texcoord;

uniform vec2 textureSize;
uniform float blurSize : 1.0;

uniform int direction: 0.0;

#ifdef DEPTHTEX_ENABLED
uniform sampler2D depthTex;
uniform mat4 projection;
uniform float depthRange : 0.5;

float getLinearDepth(vec2 coord)
{
 float depth = texture2D(depthTex, coord).r * 2.0 - 1.0;
 return projection[3][2] / (depth * projection[2][3] - projection[2][2]);
}
#endif

void main()
{
 float kernel[5];
 kernel[0] = 0.122581;
 kernel[1] = 0.233062;
 kernel[2] = 0.288713;
 kernel[3] = 0.233062;
 kernel[4] = 0.122581;

 vec2 off = vec2(0.0);
 if (direction == 0) {
 off[0] = blurSize / textureSize.x;
 }
 else {
 off[1] = blurSize / textureSize.y;
 }

 vec2 coord = v_Texcoord;

 float sum = 0.0;
 float weightAll = 0.0;

#ifdef NORMALTEX_ENABLED
 vec3 centerNormal = texture2D(normalTex, v_Texcoord).rgb * 2.0 - 1.0;
#endif
#if defined(DEPTHTEX_ENABLED)
 float centerDepth = getLinearDepth(v_Texcoord);
#endif

 for (int i = 0; i < 5; i++) {
 vec2 coord = clamp(v_Texcoord + vec2(float(i) - 2.0) * off, vec2(0.0), vec2(1.0));

 float w = kernel[i];
#ifdef NORMALTEX_ENABLED
 vec3 normal = texture2D(normalTex, coord).rgb * 2.0 - 1.0;
 w *= clamp(dot(normal, centerNormal), 0.0, 1.0);
#endif
#ifdef DEPTHTEX_ENABLED
 float d = getLinearDepth(coord);
 w *= (1.0 - smoothstep(abs(centerDepth - d) / depthRange, 0.0, 1.0));
#endif

 weightAll += w;
 sum += texture2D(ssaoTexture, coord).r * w;
 }

 gl_FragColor = vec4(vec3(sum / weightAll), 1.0);
}

@end
`);function Ho(e){for(var t=new Uint8Array(e*e*4),n=0,r=new L,i=0;i<e;i++)for(var a=0;a<e;a++)r.set(Math.random()*2-1,Math.random()*2-1,0).normalize(),t[n++]=(r.x*.5+.5)*255,t[n++]=(r.y*.5+.5)*255,t[n++]=0,t[n++]=255;return t}function Uo(e){return new J({pixels:Ho(e),wrapS:q.REPEAT,wrapT:q.REPEAT,width:e,height:e})}function Wo(e,t,n){var r=new Float32Array(e*3);t=t||0;for(var i=0;i<e;i++){var a=Vo(i+t,2)*(n?1:2)*Math.PI,o=Vo(i+t,3)*Math.PI,s=Math.random(),c=Math.cos(a)*Math.sin(o)*s,l=Math.cos(o)*s,u=Math.sin(a)*Math.sin(o)*s;r[i*3]=c,r[i*3+1]=l,r[i*3+2]=u}return r}function Go(e){e=e||{},this._ssaoPass=new bi({fragment:K.source(`ecgl.ssao.estimate`)}),this._blurPass=new bi({fragment:K.source(`ecgl.ssao.blur`)}),this._framebuffer=new Or({depthBuffer:!1}),this._ssaoTexture=new J,this._blurTexture=new J,this._blurTexture2=new J,this._depthTex=e.depthTexture,this._normalTex=e.normalTexture,this.setNoiseSize(4),this.setKernelSize(e.kernelSize||12),e.radius!=null&&this.setParameter(`radius`,e.radius),e.power!=null&&this.setParameter(`power`,e.power),this._normalTex||(this._ssaoPass.material.disableTexture(`normalTex`),this._blurPass.material.disableTexture(`normalTex`)),this._depthTex||this._blurPass.material.disableTexture(`depthTex`),this._blurPass.material.setUniform(`normalTex`,this._normalTex),this._blurPass.material.setUniform(`depthTex`,this._depthTex)}Go.prototype.setDepthTexture=function(e){this._depthTex=e},Go.prototype.setNormalTexture=function(e){this._normalTex=e,this._ssaoPass.material[e?`enableTexture`:`disableTexture`](`normalTex`),this.setKernelSize(this._kernelSize)},Go.prototype.update=function(e,t,n){var r=e.getWidth(),i=e.getHeight(),a=this._ssaoPass,o=this._blurPass;a.setUniform(`kernel`,this._kernels[n%this._kernels.length]),a.setUniform(`depthTex`,this._depthTex),this._normalTex!=null&&a.setUniform(`normalTex`,this._normalTex),a.setUniform(`depthTexSize`,[this._depthTex.width,this._depthTex.height]);var s=new H;H.transpose(s,t.worldTransform),a.setUniform(`projection`,t.projectionMatrix.array),a.setUniform(`projectionInv`,t.invProjectionMatrix.array),a.setUniform(`viewInverseTranspose`,s.array);var c=this._ssaoTexture,l=this._blurTexture,u=this._blurTexture2;c.width=r/2,c.height=i/2,l.width=r,l.height=i,u.width=r,u.height=i,this._framebuffer.attach(c),this._framebuffer.bind(e),e.gl.clearColor(1,1,1,1),e.gl.clear(e.gl.COLOR_BUFFER_BIT),a.render(e),o.setUniform(`textureSize`,[r/2,i/2]),o.setUniform(`projection`,t.projectionMatrix.array),this._framebuffer.attach(l),o.setUniform(`direction`,0),o.setUniform(`ssaoTexture`,c),o.render(e),this._framebuffer.attach(u),o.setUniform(`textureSize`,[r,i]),o.setUniform(`direction`,1),o.setUniform(`ssaoTexture`,l),o.render(e),this._framebuffer.unbind(e);var d=e.clearColor;e.gl.clearColor(d[0],d[1],d[2],d[3])},Go.prototype.getTargetTexture=function(){return this._blurTexture2},Go.prototype.setParameter=function(e,t){e===`noiseTexSize`?this.setNoiseSize(t):e===`kernelSize`?this.setKernelSize(t):e===`intensity`?this._ssaoPass.material.set(`intensity`,t):this._ssaoPass.setUniform(e,t)},Go.prototype.setKernelSize=function(e){this._kernelSize=e,this._ssaoPass.material.define(`fragment`,`KERNEL_SIZE`,e),this._kernels=this._kernels||[];for(var t=0;t<30;t++)this._kernels[t]=Wo(e,t*e,!!this._normalTex)},Go.prototype.setNoiseSize=function(e){var t=this._ssaoPass.getUniform(`noiseTex`);t?(t.data=Ho(e),t.width=t.height=e,t.dirty()):(t=Uo(e),this._ssaoPass.setUniform(`noiseTex`,Uo(e))),this._ssaoPass.setUniform(`noiseTexSize`,[e,e])},Go.prototype.dispose=function(e){this._blurTexture.dispose(e),this._ssaoTexture.dispose(e),this._blurTexture2.dispose(e)},K.import(`@export ecgl.ssr.main

#define SHADER_NAME SSR
#define MAX_ITERATION 20;
#define SAMPLE_PER_FRAME 5;
#define TOTAL_SAMPLES 128;

uniform sampler2D sourceTexture;
uniform sampler2D gBufferTexture1;
uniform sampler2D gBufferTexture2;
uniform sampler2D gBufferTexture3;
uniform samplerCube specularCubemap;
uniform float specularIntensity: 1;

uniform mat4 projection;
uniform mat4 projectionInv;
uniform mat4 toViewSpace;
uniform mat4 toWorldSpace;

uniform float maxRayDistance: 200;

uniform float pixelStride: 16;
uniform float pixelStrideZCutoff: 50; 
uniform float screenEdgeFadeStart: 0.9; 
uniform float eyeFadeStart : 0.2; uniform float eyeFadeEnd: 0.8; 
uniform float minGlossiness: 0.2; uniform float zThicknessThreshold: 1;

uniform float nearZ;
uniform vec2 viewportSize : VIEWPORT_SIZE;

uniform float jitterOffset: 0;

varying vec2 v_Texcoord;

#ifdef DEPTH_DECODE
@import clay.util.decode_float
#endif

#ifdef PHYSICALLY_CORRECT
uniform sampler2D normalDistribution;
uniform float sampleOffset: 0;
uniform vec2 normalDistributionSize;

vec3 transformNormal(vec3 H, vec3 N) {
 vec3 upVector = N.y > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
 vec3 tangentX = normalize(cross(N, upVector));
 vec3 tangentZ = cross(N, tangentX);
 return normalize(tangentX * H.x + N * H.y + tangentZ * H.z);
}
vec3 importanceSampleNormalGGX(float i, float roughness, vec3 N) {
 float p = fract((i + sampleOffset) / float(TOTAL_SAMPLES));
 vec3 H = texture2D(normalDistribution,vec2(roughness, p)).rgb;
 return transformNormal(H, N);
}
float G_Smith(float g, float ndv, float ndl) {
 float roughness = 1.0 - g;
 float k = roughness * roughness / 2.0;
 float G1V = ndv / (ndv * (1.0 - k) + k);
 float G1L = ndl / (ndl * (1.0 - k) + k);
 return G1L * G1V;
}
vec3 F_Schlick(float ndv, vec3 spec) {
 return spec + (1.0 - spec) * pow(1.0 - ndv, 5.0);
}
#endif

float fetchDepth(sampler2D depthTexture, vec2 uv)
{
 vec4 depthTexel = texture2D(depthTexture, uv);
 return depthTexel.r * 2.0 - 1.0;
}

float linearDepth(float depth)
{
 if (projection[3][3] == 0.0) {
 return projection[3][2] / (depth * projection[2][3] - projection[2][2]);
 }
 else {
 return (depth - projection[3][2]) / projection[2][2];
 }
}

bool rayIntersectDepth(float rayZNear, float rayZFar, vec2 hitPixel)
{
 if (rayZFar > rayZNear)
 {
 float t = rayZFar; rayZFar = rayZNear; rayZNear = t;
 }
 float cameraZ = linearDepth(fetchDepth(gBufferTexture2, hitPixel));
 return rayZFar <= cameraZ && rayZNear >= cameraZ - zThicknessThreshold;
}


bool traceScreenSpaceRay(
 vec3 rayOrigin, vec3 rayDir, float jitter,
 out vec2 hitPixel, out vec3 hitPoint, out float iterationCount
)
{
 float rayLength = ((rayOrigin.z + rayDir.z * maxRayDistance) > -nearZ)
 ? (-nearZ - rayOrigin.z) / rayDir.z : maxRayDistance;

 vec3 rayEnd = rayOrigin + rayDir * rayLength;

 vec4 H0 = projection * vec4(rayOrigin, 1.0);
 vec4 H1 = projection * vec4(rayEnd, 1.0);

 float k0 = 1.0 / H0.w, k1 = 1.0 / H1.w;

 vec3 Q0 = rayOrigin * k0, Q1 = rayEnd * k1;

 vec2 P0 = (H0.xy * k0 * 0.5 + 0.5) * viewportSize;
 vec2 P1 = (H1.xy * k1 * 0.5 + 0.5) * viewportSize;

 P1 += dot(P1 - P0, P1 - P0) < 0.0001 ? 0.01 : 0.0;
 vec2 delta = P1 - P0;

 bool permute = false;
 if (abs(delta.x) < abs(delta.y)) {
 permute = true;
 delta = delta.yx;
 P0 = P0.yx;
 P1 = P1.yx;
 }
 float stepDir = sign(delta.x);
 float invdx = stepDir / delta.x;

 vec3 dQ = (Q1 - Q0) * invdx;
 float dk = (k1 - k0) * invdx;

 vec2 dP = vec2(stepDir, delta.y * invdx);

 float strideScaler = 1.0 - min(1.0, -rayOrigin.z / pixelStrideZCutoff);
 float pixStride = 1.0 + strideScaler * pixelStride;

 dP *= pixStride; dQ *= pixStride; dk *= pixStride;

 vec4 pqk = vec4(P0, Q0.z, k0);
 vec4 dPQK = vec4(dP, dQ.z, dk);

 pqk += dPQK * jitter;
 float rayZFar = (dPQK.z * 0.5 + pqk.z) / (dPQK.w * 0.5 + pqk.w);
 float rayZNear;

 bool intersect = false;

 vec2 texelSize = 1.0 / viewportSize;

 iterationCount = 0.0;

 for (int i = 0; i < MAX_ITERATION; i++)
 {
 pqk += dPQK;

 rayZNear = rayZFar;
 rayZFar = (dPQK.z * 0.5 + pqk.z) / (dPQK.w * 0.5 + pqk.w);

 hitPixel = permute ? pqk.yx : pqk.xy;
 hitPixel *= texelSize;

 intersect = rayIntersectDepth(rayZNear, rayZFar, hitPixel);

 iterationCount += 1.0;

 dPQK *= 1.2;

 if (intersect) {
 break;
 }
 }

 Q0.xy += dQ.xy * iterationCount;
 Q0.z = pqk.z;
 hitPoint = Q0 / pqk.w;

 return intersect;
}

float calculateAlpha(
 float iterationCount, float reflectivity,
 vec2 hitPixel, vec3 hitPoint, float dist, vec3 rayDir
)
{
 float alpha = clamp(reflectivity, 0.0, 1.0);
 alpha *= 1.0 - (iterationCount / float(MAX_ITERATION));
 vec2 hitPixelNDC = hitPixel * 2.0 - 1.0;
 float maxDimension = min(1.0, max(abs(hitPixelNDC.x), abs(hitPixelNDC.y)));
 alpha *= 1.0 - max(0.0, maxDimension - screenEdgeFadeStart) / (1.0 - screenEdgeFadeStart);

 float _eyeFadeStart = eyeFadeStart;
 float _eyeFadeEnd = eyeFadeEnd;
 if (_eyeFadeStart > _eyeFadeEnd) {
 float tmp = _eyeFadeEnd;
 _eyeFadeEnd = _eyeFadeStart;
 _eyeFadeStart = tmp;
 }

 float eyeDir = clamp(rayDir.z, _eyeFadeStart, _eyeFadeEnd);
 alpha *= 1.0 - (eyeDir - _eyeFadeStart) / (_eyeFadeEnd - _eyeFadeStart);

 alpha *= 1.0 - clamp(dist / maxRayDistance, 0.0, 1.0);

 return alpha;
}

@import clay.util.rand

@import clay.util.rgbm

void main()
{
 vec4 normalAndGloss = texture2D(gBufferTexture1, v_Texcoord);

 if (dot(normalAndGloss.rgb, vec3(1.0)) == 0.0) {
 discard;
 }

 float g = normalAndGloss.a;
#if !defined(PHYSICALLY_CORRECT)
 if (g <= minGlossiness) {
 discard;
 }
#endif

 float reflectivity = (g - minGlossiness) / (1.0 - minGlossiness);

 vec3 N = normalize(normalAndGloss.rgb * 2.0 - 1.0);
 N = normalize((toViewSpace * vec4(N, 0.0)).xyz);

 vec4 projectedPos = vec4(v_Texcoord * 2.0 - 1.0, fetchDepth(gBufferTexture2, v_Texcoord), 1.0);
 vec4 pos = projectionInv * projectedPos;
 vec3 rayOrigin = pos.xyz / pos.w;
 vec3 V = -normalize(rayOrigin);

 float ndv = clamp(dot(N, V), 0.0, 1.0);
 float iterationCount;
 float jitter = rand(fract(v_Texcoord + jitterOffset));

#ifdef PHYSICALLY_CORRECT
 vec4 color = vec4(vec3(0.0), 1.0);
 vec4 albedoMetalness = texture2D(gBufferTexture3, v_Texcoord);
 vec3 albedo = albedoMetalness.rgb;
 float m = albedoMetalness.a;
 vec3 diffuseColor = albedo * (1.0 - m);
 vec3 spec = mix(vec3(0.04), albedo, m);

 float jitter2 = rand(fract(v_Texcoord)) * float(TOTAL_SAMPLES);

 for (int i = 0; i < SAMPLE_PER_FRAME; i++) {
 vec3 H = importanceSampleNormalGGX(float(i) + jitter2, 1.0 - g, N);
 vec3 rayDir = normalize(reflect(-V, H));
#else
 vec3 rayDir = normalize(reflect(-V, N));
#endif
 vec2 hitPixel;
 vec3 hitPoint;

 bool intersect = traceScreenSpaceRay(rayOrigin, rayDir, jitter, hitPixel, hitPoint, iterationCount);

 float dist = distance(rayOrigin, hitPoint);

 vec3 hitNormal = texture2D(gBufferTexture1, hitPixel).rgb * 2.0 - 1.0;
 hitNormal = normalize((toViewSpace * vec4(hitNormal, 0.0)).xyz);
#ifdef PHYSICALLY_CORRECT
 float ndl = clamp(dot(N, rayDir), 0.0, 1.0);
 float vdh = clamp(dot(V, H), 0.0, 1.0);
 float ndh = clamp(dot(N, H), 0.0, 1.0);
 vec3 litTexel = vec3(0.0);
 if (dot(hitNormal, rayDir) < 0.0 && intersect) {
 litTexel = texture2D(sourceTexture, hitPixel).rgb;
 litTexel *= pow(clamp(1.0 - dist / 200.0, 0.0, 1.0), 3.0);

 }
 else {
 #ifdef SPECULARCUBEMAP_ENABLED
 vec3 rayDirW = normalize(toWorldSpace * vec4(rayDir, 0.0)).rgb;
 litTexel = RGBMDecode(textureCubeLodEXT(specularCubemap, rayDirW, 0.0), 8.12).rgb * specularIntensity;
#endif
 }
 color.rgb += ndl * litTexel * (
 F_Schlick(ndl, spec) * G_Smith(g, ndv, ndl) * vdh / (ndh * ndv + 0.001)
 );
 }
 color.rgb /= float(SAMPLE_PER_FRAME);
#else
 #if !defined(SPECULARCUBEMAP_ENABLED)
 if (dot(hitNormal, rayDir) >= 0.0) {
 discard;
 }
 if (!intersect) {
 discard;
 }
#endif
 float alpha = clamp(calculateAlpha(iterationCount, reflectivity, hitPixel, hitPoint, dist, rayDir), 0.0, 1.0);
 vec4 color = texture2D(sourceTexture, hitPixel);
 color.rgb *= alpha;

#ifdef SPECULARCUBEMAP_ENABLED
 vec3 rayDirW = normalize(toWorldSpace * vec4(rayDir, 0.0)).rgb;
 alpha = alpha * (intersect ? 1.0 : 0.0);
 float bias = (1.0 -g) * 5.0;
 color.rgb += (1.0 - alpha)
 * RGBMDecode(textureCubeLodEXT(specularCubemap, rayDirW, bias), 8.12).rgb
 * specularIntensity;
#endif

#endif

 gl_FragColor = encodeHDR(color);
}
@end

@export ecgl.ssr.blur

uniform sampler2D texture;
uniform sampler2D gBufferTexture1;
uniform sampler2D gBufferTexture2;
uniform mat4 projection;
uniform float depthRange : 0.05;

varying vec2 v_Texcoord;

uniform vec2 textureSize;
uniform float blurSize : 1.0;

#ifdef BLEND
 #ifdef SSAOTEX_ENABLED
uniform sampler2D ssaoTex;
 #endif
uniform sampler2D sourceTexture;
#endif

float getLinearDepth(vec2 coord)
{
 float depth = texture2D(gBufferTexture2, coord).r * 2.0 - 1.0;
 return projection[3][2] / (depth * projection[2][3] - projection[2][2]);
}

@import clay.util.rgbm


void main()
{
 @import clay.compositor.kernel.gaussian_9

 vec4 centerNTexel = texture2D(gBufferTexture1, v_Texcoord);
 float g = centerNTexel.a;
 float maxBlurSize = clamp(1.0 - g, 0.0, 1.0) * blurSize;
#ifdef VERTICAL
 vec2 off = vec2(0.0, maxBlurSize / textureSize.y);
#else
 vec2 off = vec2(maxBlurSize / textureSize.x, 0.0);
#endif

 vec2 coord = v_Texcoord;

 vec4 sum = vec4(0.0);
 float weightAll = 0.0;

 vec3 cN = centerNTexel.rgb * 2.0 - 1.0;
 float cD = getLinearDepth(v_Texcoord);
 for (int i = 0; i < 9; i++) {
 vec2 coord = clamp((float(i) - 4.0) * off + v_Texcoord, vec2(0.0), vec2(1.0));
 float w = gaussianKernel[i]
 * clamp(dot(cN, texture2D(gBufferTexture1, coord).rgb * 2.0 - 1.0), 0.0, 1.0);
 float d = getLinearDepth(coord);
 w *= (1.0 - smoothstep(abs(cD - d) / depthRange, 0.0, 1.0));

 weightAll += w;
 sum += decodeHDR(texture2D(texture, coord)) * w;
 }

#ifdef BLEND
 float aoFactor = 1.0;
 #ifdef SSAOTEX_ENABLED
 aoFactor = texture2D(ssaoTex, v_Texcoord).r;
 #endif
 gl_FragColor = encodeHDR(
 sum / weightAll * aoFactor + decodeHDR(texture2D(sourceTexture, v_Texcoord))
 );
#else
 gl_FragColor = encodeHDR(sum / weightAll);
#endif
}

@end`);function Ko(e){e=e||{},this._ssrPass=new bi({fragment:K.source(`ecgl.ssr.main`),clearColor:[0,0,0,0]}),this._blurPass1=new bi({fragment:K.source(`ecgl.ssr.blur`),clearColor:[0,0,0,0]}),this._blurPass2=new bi({fragment:K.source(`ecgl.ssr.blur`),clearColor:[0,0,0,0]}),this._blendPass=new bi({fragment:K.source(`clay.compositor.blend`)}),this._blendPass.material.disableTexturesAll(),this._blendPass.material.enableTexture([`texture1`,`texture2`]),this._ssrPass.setUniform(`gBufferTexture1`,e.normalTexture),this._ssrPass.setUniform(`gBufferTexture2`,e.depthTexture),this._blurPass1.setUniform(`gBufferTexture1`,e.normalTexture),this._blurPass1.setUniform(`gBufferTexture2`,e.depthTexture),this._blurPass2.setUniform(`gBufferTexture1`,e.normalTexture),this._blurPass2.setUniform(`gBufferTexture2`,e.depthTexture),this._blurPass2.material.define(`fragment`,`VERTICAL`),this._blurPass2.material.define(`fragment`,`BLEND`),this._ssrTexture=new J({type:q.HALF_FLOAT}),this._texture2=new J({type:q.HALF_FLOAT}),this._texture3=new J({type:q.HALF_FLOAT}),this._prevTexture=new J({type:q.HALF_FLOAT}),this._currentTexture=new J({type:q.HALF_FLOAT}),this._frameBuffer=new Or({depthBuffer:!1}),this._normalDistribution=null,this._totalSamples=256,this._samplePerFrame=4,this._ssrPass.material.define(`fragment`,`SAMPLE_PER_FRAME`,this._samplePerFrame),this._ssrPass.material.define(`fragment`,`TOTAL_SAMPLES`,this._totalSamples),this._downScale=1}Ko.prototype.setAmbientCubemap=function(e,t){this._ssrPass.material.set(`specularCubemap`,e),this._ssrPass.material.set(`specularIntensity`,t);var n=e&&t;this._ssrPass.material[n?`enableTexture`:`disableTexture`](`specularCubemap`)},Ko.prototype.update=function(e,t,n,r){var i=e.getWidth(),a=e.getHeight(),o=this._ssrTexture,s=this._texture2,c=this._texture3;o.width=this._prevTexture.width=this._currentTexture.width=i/this._downScale,o.height=this._prevTexture.height=this._currentTexture.height=a/this._downScale,s.width=c.width=i,s.height=c.height=a;var l=this._frameBuffer,u=this._ssrPass,d=this._blurPass1,f=this._blurPass2,p=this._blendPass,m=new H,h=new H;H.transpose(m,t.worldTransform),H.transpose(h,t.viewMatrix),u.setUniform(`sourceTexture`,n),u.setUniform(`projection`,t.projectionMatrix.array),u.setUniform(`projectionInv`,t.invProjectionMatrix.array),u.setUniform(`toViewSpace`,m.array),u.setUniform(`toWorldSpace`,h.array),u.setUniform(`nearZ`,t.near);var g=r/this._totalSamples*this._samplePerFrame;if(u.setUniform(`jitterOffset`,g),u.setUniform(`sampleOffset`,r*this._samplePerFrame),d.setUniform(`textureSize`,[o.width,o.height]),f.setUniform(`textureSize`,[i,a]),f.setUniform(`sourceTexture`,n),d.setUniform(`projection`,t.projectionMatrix.array),f.setUniform(`projection`,t.projectionMatrix.array),l.attach(o),l.bind(e),u.render(e),this._physicallyCorrect&&(l.attach(this._currentTexture),p.setUniform(`texture1`,this._prevTexture),p.setUniform(`texture2`,o),p.material.set({weight1:r>=1?.95:0,weight2:r>=1?.05:1}),p.render(e)),l.attach(s),d.setUniform(`texture`,this._physicallyCorrect?this._currentTexture:o),d.render(e),l.attach(c),f.setUniform(`texture`,s),f.render(e),l.unbind(e),this._physicallyCorrect){var _=this._prevTexture;this._prevTexture=this._currentTexture,this._currentTexture=_}},Ko.prototype.getTargetTexture=function(){return this._texture3},Ko.prototype.setParameter=function(e,t){e===`maxIteration`?this._ssrPass.material.define(`fragment`,`MAX_ITERATION`,t):this._ssrPass.setUniform(e,t)},Ko.prototype.setPhysicallyCorrect=function(e){e?(this._normalDistribution||(this._normalDistribution=Ci.generateNormalDistribution(64,this._totalSamples)),this._ssrPass.material.define(`fragment`,`PHYSICALLY_CORRECT`),this._ssrPass.material.set(`normalDistribution`,this._normalDistribution),this._ssrPass.material.set(`normalDistributionSize`,[64,this._totalSamples])):this._ssrPass.material.undefine(`fragment`,`PHYSICALLY_CORRECT`),this._physicallyCorrect=e},Ko.prototype.setSSAOTexture=function(e){var t=this._blurPass2;e?(t.material.enableTexture(`ssaoTex`),t.material.set(`ssaoTex`,e)):t.material.disableTexture(`ssaoTex`)},Ko.prototype.isFinished=function(e){return!this._physicallyCorrect||e>this._totalSamples/this._samplePerFrame},Ko.prototype.dispose=function(e){this._ssrTexture.dispose(e),this._texture2.dispose(e),this._texture3.dispose(e),this._prevTexture.dispose(e),this._currentTexture.dispose(e),this._frameBuffer.dispose(e)};var qo=[0,0,-.321585265978,-.154972575841,.458126042375,.188473391593,.842080129861,.527766490688,.147304551086,-.659453822776,-.331943915203,-.940619700594,.0479226680259,.54812163202,.701581552186,-.709825561388,-.295436780218,.940589268233,-.901489676764,.237713156085,.973570876096,-.109899459384,-.866792314779,-.451805525005,.330975007087,.800048655954,-.344275183665,.381779221166,-.386139432542,-.437418421534,-.576478634965,-.0148463392551,.385798197415,-.262426961053,-.666302061145,.682427250835,-.628010632582,-.732836215494,.10163141741,-.987658134403,.711995289051,-.320024291314,.0296005138058,.950296523438,.0130612307608,-.351024443122,-.879596633704,-.10478487883,.435712737232,.504254490347,.779203817497,.206477676721,.388264289969,-.896736162545,-.153106280781,-.629203242522,-.245517550697,.657969239148,.126830499058,.26862328493,-.634888119007,-.302301223431,.617074219636,.779817204925];K.import(`@export ecgl.normal.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header

@import ecgl.common.attributes

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

@import ecgl.common.normalMap.vertexHeader

@import ecgl.common.vertexAnimation.header

void main()
{

 @import ecgl.common.vertexAnimation.main

 @import ecgl.common.uv.main

 v_Normal = normalize((worldInverseTranspose * vec4(normal, 0.0)).xyz);
 v_WorldPosition = (world * vec4(pos, 1.0)).xyz;

 @import ecgl.common.normalMap.vertexMain

 gl_Position = worldViewProjection * vec4(pos, 1.0);

}


@end


@export ecgl.normal.fragment

#define ROUGHNESS_CHANEL 0

uniform bool useBumpMap;
uniform bool useRoughnessMap;
uniform bool doubleSide;
uniform float roughness;

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform mat4 viewInverse : VIEWINVERSE;

@import ecgl.common.normalMap.fragmentHeader
@import ecgl.common.bumpMap.header

uniform sampler2D roughnessMap;

void main()
{
 vec3 N = v_Normal;
 
 bool flipNormal = false;
 if (doubleSide) {
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);

 if (dot(N, V) < 0.0) {
 flipNormal = true;
 }
 }

 @import ecgl.common.normalMap.fragmentMain

 if (useBumpMap) {
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 }

 float g = 1.0 - roughness;

 if (useRoughnessMap) {
 float g2 = 1.0 - texture2D(roughnessMap, v_DetailTexcoord)[ROUGHNESS_CHANEL];
 g = clamp(g2 + (g - 0.5) * 2.0, 0.0, 1.0);
 }

 if (flipNormal) {
 N = -N;
 }

 gl_FragColor.rgb = (N.xyz + 1.0) * 0.5;
 gl_FragColor.a = g;
}
@end`);function Jo(e,t,n,r,i){var a=e.gl;t.setUniform(a,`1i`,n,i),a.activeTexture(a.TEXTURE0+i),r.isRenderable()?r.bind(e):r.unbind(e)}function Yo(e,t,n,r,i){var a,o,s,c,l=e.gl;return function(i,u,d){if(!(c&&c.material===i.material)){var f=i.material,p=i.__program,m=f.get(`roughness`);m==null&&(m=1);var h=f.get(`normalMap`)||t,g=f.get(`roughnessMap`),_=f.get(`bumpMap`),v=f.get(`uvRepeat`),y=f.get(`uvOffset`),b=f.get(`detailUvRepeat`),x=f.get(`detailUvOffset`),S=!!_&&f.isTextureEnabled(`bumpMap`),C=!!g&&f.isTextureEnabled(`roughnessMap`),w=f.isDefined(`fragment`,`DOUBLE_SIDED`);_=_||n,g=g||r,d===u?(p.setUniform(l,`1f`,`roughness`,m),a!==h&&Jo(e,p,`normalMap`,h,0),o!==_&&_&&Jo(e,p,`bumpMap`,_,1),s!==g&&g&&Jo(e,p,`roughnessMap`,g,2),v!=null&&p.setUniform(l,`2f`,`uvRepeat`,v),y!=null&&p.setUniform(l,`2f`,`uvOffset`,y),b!=null&&p.setUniform(l,`2f`,`detailUvRepeat`,b),x!=null&&p.setUniform(l,`2f`,`detailUvOffset`,x),p.setUniform(l,`1i`,`useBumpMap`,+S),p.setUniform(l,`1i`,`useRoughnessMap`,+C),p.setUniform(l,`1i`,`doubleSide`,+w)):(u.set(`normalMap`,h),u.set(`bumpMap`,_),u.set(`roughnessMap`,g),u.set(`useBumpMap`,S),u.set(`useRoughnessMap`,C),u.set(`doubleSide`,w),v!=null&&u.set(`uvRepeat`,v),y!=null&&u.set(`uvOffset`,y),b!=null&&u.set(`detailUvRepeat`,b),x!=null&&u.set(`detailUvOffset`,x),u.set(`roughness`,m)),a=h,o=_,s=g,c=i}}}function Xo(e){e=e||{},this._depthTex=new J({format:q.DEPTH_COMPONENT,type:q.UNSIGNED_INT}),this._normalTex=new J({type:q.HALF_FLOAT}),this._framebuffer=new Or,this._framebuffer.attach(this._normalTex),this._framebuffer.attach(this._depthTex,Or.DEPTH_ATTACHMENT),this._normalMaterial=new Mt({shader:new K(K.source(`ecgl.normal.vertex`),K.source(`ecgl.normal.fragment`))}),this._normalMaterial.enableTexture([`normalMap`,`bumpMap`,`roughnessMap`]),this._defaultNormalMap=di.createBlank(`#000`),this._defaultBumpMap=di.createBlank(`#000`),this._defaultRoughessMap=di.createBlank(`#000`),this._debugPass=new bi({fragment:K.source(`clay.compositor.output`)}),this._debugPass.setUniform(`texture`,this._normalTex),this._debugPass.material.undefine(`fragment`,`OUTPUT_ALPHA`)}Xo.prototype.getDepthTexture=function(){return this._depthTex},Xo.prototype.getNormalTexture=function(){return this._normalTex},Xo.prototype.update=function(e,t,n){var r=e.getWidth(),i=e.getHeight(),a=this._depthTex,o=this._normalTex,s=this._normalMaterial;a.width=r,a.height=i,o.width=r,o.height=i;var c=t.getRenderList(n).opaque;this._framebuffer.bind(e),e.gl.clearColor(0,0,0,0),e.gl.clear(e.gl.COLOR_BUFFER_BIT|e.gl.DEPTH_BUFFER_BIT),e.gl.disable(e.gl.BLEND),e.renderPass(c,n,{getMaterial:function(){return s},ifRender:function(e){return e.renderNormal},beforeRender:Yo(e,this._defaultNormalMap,this._defaultBumpMap,this._defaultRoughessMap,this._normalMaterial),sort:e.opaqueSortCompare}),this._framebuffer.unbind(e)},Xo.prototype.renderDebug=function(e){this._debugPass.render(e)},Xo.prototype.dispose=function(e){this._depthTex.dispose(e),this._normalTex.dispose(e)};function Zo(e){e=e||{},this._edgePass=new bi({fragment:K.source(`ecgl.edge`)}),this._edgePass.setUniform(`normalTexture`,e.normalTexture),this._edgePass.setUniform(`depthTexture`,e.depthTexture),this._targetTexture=new J({type:q.HALF_FLOAT}),this._frameBuffer=new Or,this._frameBuffer.attach(this._targetTexture)}Zo.prototype.update=function(e,t,n,r){var i=e.getWidth(),a=e.getHeight(),o=this._targetTexture;o.width=i,o.height=a;var s=this._frameBuffer;s.bind(e),this._edgePass.setUniform(`projectionInv`,t.invProjectionMatrix.array),this._edgePass.setUniform(`textureSize`,[i,a]),this._edgePass.setUniform(`texture`,n),this._edgePass.render(e),s.unbind(e)},Zo.prototype.getTargetTexture=function(){return this._targetTexture},Zo.prototype.setParameter=function(e,t){this._edgePass.setUniform(e,t)},Zo.prototype.dispose=function(e){this._targetTexture.dispose(e),this._frameBuffer.dispose(e)};var Qo={type:`compositor`,nodes:[{name:`source`,type:`texture`,outputs:{color:{}}},{name:`source_half`,shader:`#source(clay.compositor.downsample)`,inputs:{texture:`source`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 2)`,height:`expr(height * 1.0 / 2)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0, height * 1.0] )`}},{name:`bright`,shader:`#source(clay.compositor.bright)`,inputs:{texture:`source_half`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 2)`,height:`expr(height * 1.0 / 2)`,type:`HALF_FLOAT`}}},parameters:{threshold:2,scale:4,textureSize:`expr([width * 1.0 / 2, height / 2])`}},{name:`bright_downsample_4`,shader:`#source(clay.compositor.downsample)`,inputs:{texture:`bright`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 4)`,height:`expr(height * 1.0 / 4)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0 / 2, height / 2] )`}},{name:`bright_downsample_8`,shader:`#source(clay.compositor.downsample)`,inputs:{texture:`bright_downsample_4`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 8)`,height:`expr(height * 1.0 / 8)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0 / 4, height / 4] )`}},{name:`bright_downsample_16`,shader:`#source(clay.compositor.downsample)`,inputs:{texture:`bright_downsample_8`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 16)`,height:`expr(height * 1.0 / 16)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0 / 8, height / 8] )`}},{name:`bright_downsample_32`,shader:`#source(clay.compositor.downsample)`,inputs:{texture:`bright_downsample_16`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 32)`,height:`expr(height * 1.0 / 32)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0 / 16, height / 16] )`}},{name:`bright_upsample_16_blur_h`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_downsample_32`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 16)`,height:`expr(height * 1.0 / 16)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:0,textureSize:`expr( [width * 1.0 / 32, height / 32] )`}},{name:`bright_upsample_16_blur_v`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_upsample_16_blur_h`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 16)`,height:`expr(height * 1.0 / 16)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:1,textureSize:`expr( [width * 1.0 / 16, height * 1.0 / 16] )`}},{name:`bright_upsample_8_blur_h`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_downsample_16`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 8)`,height:`expr(height * 1.0 / 8)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:0,textureSize:`expr( [width * 1.0 / 16, height * 1.0 / 16] )`}},{name:`bright_upsample_8_blur_v`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_upsample_8_blur_h`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 8)`,height:`expr(height * 1.0 / 8)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:1,textureSize:`expr( [width * 1.0 / 8, height * 1.0 / 8] )`}},{name:`bright_upsample_8_blend`,shader:`#source(clay.compositor.blend)`,inputs:{texture1:`bright_upsample_8_blur_v`,texture2:`bright_upsample_16_blur_v`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 8)`,height:`expr(height * 1.0 / 8)`,type:`HALF_FLOAT`}}},parameters:{weight1:.3,weight2:.7}},{name:`bright_upsample_4_blur_h`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_downsample_8`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 4)`,height:`expr(height * 1.0 / 4)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:0,textureSize:`expr( [width * 1.0 / 8, height * 1.0 / 8] )`}},{name:`bright_upsample_4_blur_v`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_upsample_4_blur_h`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 4)`,height:`expr(height * 1.0 / 4)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:1,textureSize:`expr( [width * 1.0 / 4, height * 1.0 / 4] )`}},{name:`bright_upsample_4_blend`,shader:`#source(clay.compositor.blend)`,inputs:{texture1:`bright_upsample_4_blur_v`,texture2:`bright_upsample_8_blend`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 4)`,height:`expr(height * 1.0 / 4)`,type:`HALF_FLOAT`}}},parameters:{weight1:.3,weight2:.7}},{name:`bright_upsample_2_blur_h`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_downsample_4`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 2)`,height:`expr(height * 1.0 / 2)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:0,textureSize:`expr( [width * 1.0 / 4, height * 1.0 / 4] )`}},{name:`bright_upsample_2_blur_v`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_upsample_2_blur_h`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 2)`,height:`expr(height * 1.0 / 2)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:1,textureSize:`expr( [width * 1.0 / 2, height * 1.0 / 2] )`}},{name:`bright_upsample_2_blend`,shader:`#source(clay.compositor.blend)`,inputs:{texture1:`bright_upsample_2_blur_v`,texture2:`bright_upsample_4_blend`},outputs:{color:{parameters:{width:`expr(width * 1.0 / 2)`,height:`expr(height * 1.0 / 2)`,type:`HALF_FLOAT`}}},parameters:{weight1:.3,weight2:.7}},{name:`bright_upsample_full_blur_h`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:0,textureSize:`expr( [width * 1.0 / 2, height * 1.0 / 2] )`}},{name:`bright_upsample_full_blur_v`,shader:`#source(clay.compositor.gaussian_blur)`,inputs:{texture:`bright_upsample_full_blur_h`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`,type:`HALF_FLOAT`}}},parameters:{blurSize:1,blurDir:1,textureSize:`expr( [width * 1.0, height * 1.0] )`}},{name:`bloom_composite`,shader:`#source(clay.compositor.blend)`,inputs:{texture1:`bright_upsample_full_blur_v`,texture2:`bright_upsample_2_blend`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`,type:`HALF_FLOAT`}}},parameters:{weight1:.3,weight2:.7}},{name:`coc`,shader:`#source(ecgl.dof.coc)`,outputs:{color:{parameters:{minFilter:`NEAREST`,magFilter:`NEAREST`,width:`expr(width * 1.0)`,height:`expr(height * 1.0)`}}},parameters:{focalDist:50,focalRange:30}},{name:`dof_far_blur`,shader:`#source(ecgl.dof.diskBlur)`,inputs:{texture:`source`,coc:`coc`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0, height * 1.0] )`}},{name:`dof_near_blur`,shader:`#source(ecgl.dof.diskBlur)`,inputs:{texture:`source`,coc:`coc`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`,type:`HALF_FLOAT`}}},parameters:{textureSize:`expr( [width * 1.0, height * 1.0] )`},defines:{BLUR_NEARFIELD:null}},{name:`dof_coc_blur`,shader:`#source(ecgl.dof.diskBlur)`,inputs:{texture:`coc`},outputs:{color:{parameters:{minFilter:`NEAREST`,magFilter:`NEAREST`,width:`expr(width * 1.0)`,height:`expr(height * 1.0)`}}},parameters:{textureSize:`expr( [width * 1.0, height * 1.0] )`},defines:{BLUR_COC:null}},{name:`dof_composite`,shader:`#source(ecgl.dof.composite)`,inputs:{original:`source`,blurred:`dof_far_blur`,nearfield:`dof_near_blur`,coc:`coc`,nearcoc:`dof_coc_blur`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`,type:`HALF_FLOAT`}}}},{name:`composite`,shader:`#source(clay.compositor.hdr.composite)`,inputs:{texture:`source`,bloom:`bloom_composite`},outputs:{color:{parameters:{width:`expr(width * 1.0)`,height:`expr(height * 1.0)`}}},defines:{}},{name:`FXAA`,shader:`#source(clay.compositor.fxaa)`,inputs:{texture:`composite`}}]};K.import(_o),K.import(yo),K.import(xo),K.import(So),K.import(Co),K.import(wo),K.import(To),K.import(Do),K.import(Oo),K.import(`@export ecgl.dof.coc

uniform sampler2D depth;

uniform float zNear: 0.1;
uniform float zFar: 2000;

uniform float focalDistance: 3;
uniform float focalRange: 1;
uniform float focalLength: 30;
uniform float fstop: 2.8;

varying vec2 v_Texcoord;

@import clay.util.encode_float

void main()
{
 float z = texture2D(depth, v_Texcoord).r * 2.0 - 1.0;

 float dist = 2.0 * zNear * zFar / (zFar + zNear - z * (zFar - zNear));

 float aperture = focalLength / fstop;

 float coc;

 float uppper = focalDistance + focalRange;
 float lower = focalDistance - focalRange;
 if (dist <= uppper && dist >= lower) {
 coc = 0.5;
 }
 else {
 float focalAdjusted = dist > uppper ? uppper : lower;

 coc = abs(aperture * (focalLength * (dist - focalAdjusted)) / (dist * (focalAdjusted - focalLength)));
 coc = clamp(coc, 0.0, 2.0) / 2.00001;

 if (dist < lower) {
 coc = -coc;
 }
 coc = coc * 0.5 + 0.5;
 }

 gl_FragColor = encodeFloat(coc);
}
@end


@export ecgl.dof.composite

#define DEBUG 0

uniform sampler2D original;
uniform sampler2D blurred;
uniform sampler2D nearfield;
uniform sampler2D coc;
uniform sampler2D nearcoc;
varying vec2 v_Texcoord;

@import clay.util.rgbm
@import clay.util.float

void main()
{
 vec4 blurredColor = texture2D(blurred, v_Texcoord);
 vec4 originalColor = texture2D(original, v_Texcoord);

 float fCoc = decodeFloat(texture2D(coc, v_Texcoord));

 fCoc = abs(fCoc * 2.0 - 1.0);

 float weight = smoothstep(0.0, 1.0, fCoc);
 
#ifdef NEARFIELD_ENABLED
 vec4 nearfieldColor = texture2D(nearfield, v_Texcoord);
 float fNearCoc = decodeFloat(texture2D(nearcoc, v_Texcoord));
 fNearCoc = abs(fNearCoc * 2.0 - 1.0);

 gl_FragColor = encodeHDR(
 mix(
 nearfieldColor, mix(originalColor, blurredColor, weight),
 pow(1.0 - fNearCoc, 4.0)
 )
 );
#else
 gl_FragColor = encodeHDR(mix(originalColor, blurredColor, weight));
#endif

}

@end



@export ecgl.dof.diskBlur

#define POISSON_KERNEL_SIZE 16;

uniform sampler2D texture;
uniform sampler2D coc;
varying vec2 v_Texcoord;

uniform float blurRadius : 10.0;
uniform vec2 textureSize : [512.0, 512.0];

uniform vec2 poissonKernel[POISSON_KERNEL_SIZE];

uniform float percent;

float nrand(const in vec2 n) {
 return fract(sin(dot(n.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

@import clay.util.rgbm
@import clay.util.float


void main()
{
 vec2 offset = blurRadius / textureSize;

 float rnd = 6.28318 * nrand(v_Texcoord + 0.07 * percent );
 float cosa = cos(rnd);
 float sina = sin(rnd);
 vec4 basis = vec4(cosa, -sina, sina, cosa);

#if !defined(BLUR_NEARFIELD) && !defined(BLUR_COC)
 offset *= abs(decodeFloat(texture2D(coc, v_Texcoord)) * 2.0 - 1.0);
#endif

#ifdef BLUR_COC
 float cocSum = 0.0;
#else
 vec4 color = vec4(0.0);
#endif


 float weightSum = 0.0;

 for (int i = 0; i < POISSON_KERNEL_SIZE; i++) {
 vec2 ofs = poissonKernel[i];

 ofs = vec2(dot(ofs, basis.xy), dot(ofs, basis.zw));

 vec2 uv = v_Texcoord + ofs * offset;
 vec4 texel = texture2D(texture, uv);

 float w = 1.0;
#ifdef BLUR_COC
 float fCoc = decodeFloat(texel) * 2.0 - 1.0;
 cocSum += clamp(fCoc, -1.0, 0.0) * w;
#else
 texel = texel;
 #if !defined(BLUR_NEARFIELD)
 float fCoc = decodeFloat(texture2D(coc, uv)) * 2.0 - 1.0;
 w *= abs(fCoc);
 #endif
 texel.rgb *= texel.a;
 color += texel * w;
#endif

 weightSum += w;
 }

#ifdef BLUR_COC
 gl_FragColor = encodeFloat(clamp(cocSum / weightSum, -1.0, 0.0) * 0.5 + 0.5);
#else
 color /= weightSum;
 color.rgb /= (color.a + 0.0001);
 gl_FragColor = color;
#endif
}

@end`),K.import(`@export ecgl.edge

uniform sampler2D texture;

uniform sampler2D normalTexture;
uniform sampler2D depthTexture;

uniform mat4 projectionInv;

uniform vec2 textureSize;

uniform vec4 edgeColor: [0,0,0,0.8];

varying vec2 v_Texcoord;

vec3 packColor(vec2 coord) {
 float z = texture2D(depthTexture, coord).r * 2.0 - 1.0;
 vec4 p = vec4(v_Texcoord * 2.0 - 1.0, z, 1.0);
 vec4 p4 = projectionInv * p;

 return vec3(
 texture2D(normalTexture, coord).rg,
 -p4.z / p4.w / 5.0
 );
}

void main() {
 vec2 cc = v_Texcoord;
 vec3 center = packColor(cc);

 float size = clamp(1.0 - (center.z - 10.0) / 100.0, 0.0, 1.0) * 0.5;
 float dx = size / textureSize.x;
 float dy = size / textureSize.y;

 vec2 coord;
 vec3 topLeft = packColor(cc+vec2(-dx, -dy));
 vec3 top = packColor(cc+vec2(0.0, -dy));
 vec3 topRight = packColor(cc+vec2(dx, -dy));
 vec3 left = packColor(cc+vec2(-dx, 0.0));
 vec3 right = packColor(cc+vec2(dx, 0.0));
 vec3 bottomLeft = packColor(cc+vec2(-dx, dy));
 vec3 bottom = packColor(cc+vec2(0.0, dy));
 vec3 bottomRight = packColor(cc+vec2(dx, dy));

 vec3 v = -topLeft-2.0*top-topRight+bottomLeft+2.0*bottom+bottomRight;
 vec3 h = -bottomLeft-2.0*left-topLeft+bottomRight+2.0*right+topRight;

 float edge = sqrt(dot(h, h) + dot(v, v));

 edge = smoothstep(0.8, 1.0, edge);

 gl_FragColor = mix(texture2D(texture, v_Texcoord), vec4(edgeColor.rgb, 1.0), edgeColor.a * edge);
}
@end`);function $o(e,t){return{color:{parameters:{width:e,height:t}}}}var es=[`composite`,`FXAA`];function $(){this._width,this._height,this._dpr,this._sourceTexture=new J({type:q.HALF_FLOAT}),this._depthTexture=new J({format:q.DEPTH_COMPONENT,type:q.UNSIGNED_INT}),this._framebuffer=new Or,this._framebuffer.attach(this._sourceTexture),this._framebuffer.attach(this._depthTexture,Or.DEPTH_ATTACHMENT),this._normalPass=new Xo,this._compositor=Bo(Qo);var e=this._compositor.getNodeByName(`source`);e.texture=this._sourceTexture;var t=this._compositor.getNodeByName(`coc`);this._sourceNode=e,this._cocNode=t,this._compositeNode=this._compositor.getNodeByName(`composite`),this._fxaaNode=this._compositor.getNodeByName(`FXAA`),this._dofBlurNodes=[`dof_far_blur`,`dof_near_blur`,`dof_coc_blur`].map(function(e){return this._compositor.getNodeByName(e)},this),this._dofBlurKernel=0,this._dofBlurKernelSize=new Float32Array,this._finalNodesChain=es.map(function(e){return this._compositor.getNodeByName(e)},this);var n={normalTexture:this._normalPass.getNormalTexture(),depthTexture:this._normalPass.getDepthTexture()};this._ssaoPass=new Go(n),this._ssrPass=new Ko(n),this._edgePass=new Zo(n)}$.prototype.resize=function(e,t,n){n=n||1;var e=e*n,t=t*n,r=this._sourceTexture,i=this._depthTexture;r.width=e,r.height=t,i.width=e,i.height=t;var a={getWidth:function(){return e},getHeight:function(){return t},getDevicePixelRatio:function(){return n}};function o(e,t){if(typeof e[t]==`function`){var n=e[t].__original||e[t];e[t]=function(e){return n.call(this,a)},e[t].__original=n}}this._compositor.nodes.forEach(function(e){for(var t in e.outputs){var n=e.outputs[t].parameters;n&&(o(n,`width`),o(n,`height`))}for(var r in e.parameters)o(e.parameters,r)}),this._width=e,this._height=t,this._dpr=n},$.prototype.getWidth=function(){return this._width},$.prototype.getHeight=function(){return this._height},$.prototype._ifRenderNormalPass=function(){return this._enableSSAO||this._enableEdge||this._enableSSR},$.prototype._getPrevNode=function(e){for(var t=es.indexOf(e.name)-1,n=this._finalNodesChain[t];n&&!this._compositor.getNodeByName(n.name);)--t,n=this._finalNodesChain[t];return n},$.prototype._getNextNode=function(e){for(var t=es.indexOf(e.name)+1,n=this._finalNodesChain[t];n&&!this._compositor.getNodeByName(n.name);)t+=1,n=this._finalNodesChain[t];return n},$.prototype._addChainNode=function(e){var t=this._getPrevNode(e),n=this._getNextNode(e);t&&(e.inputs.texture=t.name,n?(e.outputs=$o(this.getWidth.bind(this),this.getHeight.bind(this)),n.inputs.texture=e.name):e.outputs=null,this._compositor.addNode(e))},$.prototype._removeChainNode=function(e){var t=this._getPrevNode(e),n=this._getNextNode(e);t&&(n?(t.outputs=$o(this.getWidth.bind(this),this.getHeight.bind(this)),n.inputs.texture=t.name):t.outputs=null,this._compositor.removeNode(e))},$.prototype.updateNormal=function(e,t,n,r){this._ifRenderNormalPass()&&this._normalPass.update(e,t,n)},$.prototype.updateSSAO=function(e,t,n,r){this._ssaoPass.update(e,n,r)},$.prototype.enableSSAO=function(){this._enableSSAO=!0},$.prototype.disableSSAO=function(){this._enableSSAO=!1},$.prototype.enableSSR=function(){this._enableSSR=!0},$.prototype.disableSSR=function(){this._enableSSR=!1},$.prototype.getSSAOTexture=function(){return this._ssaoPass.getTargetTexture()},$.prototype.getSourceFrameBuffer=function(){return this._framebuffer},$.prototype.getSourceTexture=function(){return this._sourceTexture},$.prototype.disableFXAA=function(){this._removeChainNode(this._fxaaNode)},$.prototype.enableFXAA=function(){this._addChainNode(this._fxaaNode)},$.prototype.enableBloom=function(){this._compositeNode.inputs.bloom=`bloom_composite`,this._compositor.dirty()},$.prototype.disableBloom=function(){this._compositeNode.inputs.bloom=null,this._compositor.dirty()},$.prototype.enableDOF=function(){this._compositeNode.inputs.texture=`dof_composite`,this._compositor.dirty()},$.prototype.disableDOF=function(){this._compositeNode.inputs.texture=`source`,this._compositor.dirty()},$.prototype.enableColorCorrection=function(){this._compositeNode.define(`COLOR_CORRECTION`),this._enableColorCorrection=!0},$.prototype.disableColorCorrection=function(){this._compositeNode.undefine(`COLOR_CORRECTION`),this._enableColorCorrection=!1},$.prototype.enableEdge=function(){this._enableEdge=!0},$.prototype.disableEdge=function(){this._enableEdge=!1},$.prototype.setBloomIntensity=function(e){this._compositeNode.setParameter(`bloomIntensity`,e)},$.prototype.setSSAOParameter=function(e,t){switch(e){case`quality`:var n={low:6,medium:12,high:32,ultra:62}[t]||12;this._ssaoPass.setParameter(`kernelSize`,n);break;case`radius`:this._ssaoPass.setParameter(e,t),this._ssaoPass.setParameter(`bias`,t/200);break;case`intensity`:this._ssaoPass.setParameter(e,t);break;default:}},$.prototype.setDOFParameter=function(e,t){switch(e){case`focalDistance`:case`focalRange`:case`fstop`:this._cocNode.setParameter(e,t);break;case`blurRadius`:for(var n=0;n<this._dofBlurNodes.length;n++)this._dofBlurNodes[n].setParameter(`blurRadius`,t);break;case`quality`:var r={low:4,medium:8,high:16,ultra:32}[t]||8;this._dofBlurKernelSize=r;for(var n=0;n<this._dofBlurNodes.length;n++)this._dofBlurNodes[n].pass.material.define(`POISSON_KERNEL_SIZE`,r);this._dofBlurKernel=new Float32Array(r*2);break;default:}},$.prototype.setSSRParameter=function(e,t){if(t!=null)switch(e){case`quality`:var n={low:10,medium:15,high:30,ultra:80}[t]||20,r={low:32,medium:16,high:8,ultra:4}[t]||16;this._ssrPass.setParameter(`maxIteration`,n),this._ssrPass.setParameter(`pixelStride`,r);break;case`maxRoughness`:this._ssrPass.setParameter(`minGlossiness`,Math.max(Math.min(1-t,1),0));break;case`physical`:this.setPhysicallyCorrectSSR(t);break;default:console.warn(`Unkown SSR parameter `+e)}},$.prototype.setPhysicallyCorrectSSR=function(e){this._ssrPass.setPhysicallyCorrect(e)},$.prototype.setEdgeColor=function(e){var t=Q.parseColor(e);this._edgePass.setParameter(`edgeColor`,t)},$.prototype.setExposure=function(e){this._compositeNode.setParameter(`exposure`,2**e)},$.prototype.setColorLookupTexture=function(e,t){this._compositeNode.pass.material.setTextureImage(`lut`,this._enableColorCorrection?e:`none`,t,{minFilter:Q.Texture.NEAREST,magFilter:Q.Texture.NEAREST,flipY:!1})},$.prototype.setColorCorrection=function(e,t){this._compositeNode.setParameter(e,t)},$.prototype.isSSREnabled=function(){return this._enableSSR},$.prototype.composite=function(e,t,n,r,i){var a=this._sourceTexture,o=a;this._enableEdge&&(this._edgePass.update(e,n,a,i),a=o=this._edgePass.getTargetTexture()),this._enableSSR&&(this._ssrPass.update(e,n,a,i),o=this._ssrPass.getTargetTexture(),this._ssrPass.setSSAOTexture(this._enableSSAO?this._ssaoPass.getTargetTexture():null)),this._sourceNode.texture=o,this._cocNode.setParameter(`depth`,this._depthTexture);for(var s=this._dofBlurKernel,c=this._dofBlurKernelSize,l=i%Math.floor(qo.length/2/c),u=0;u<c*2;u++)s[u]=qo[u+l*c*2];for(var u=0;u<this._dofBlurNodes.length;u++)this._dofBlurNodes[u].setParameter(`percent`,i/30),this._dofBlurNodes[u].setParameter(`poissonKernel`,s);this._cocNode.setParameter(`zNear`,n.near),this._cocNode.setParameter(`zFar`,n.far),this._compositor.render(e,r)},$.prototype.dispose=function(e){this._sourceTexture.dispose(e),this._depthTexture.dispose(e),this._framebuffer.dispose(e),this._compositor.dispose(e),this._normalPass.dispose(e),this._ssaoPass.dispose(e)};function ts(e){for(var t=[],n=0;n<30;n++)t.push([Vo(n,2),Vo(n,3)]);this._haltonSequence=t,this._frame=0,this._sourceTex=new J,this._sourceFb=new Or,this._sourceFb.attach(this._sourceTex),this._prevFrameTex=new J,this._outputTex=new J;var r=this._blendPass=new bi({fragment:K.source(`clay.compositor.blend`)});r.material.disableTexturesAll(),r.material.enableTexture([`texture1`,`texture2`]),this._blendFb=new Or({depthBuffer:!1}),this._outputPass=new bi({fragment:K.source(`clay.compositor.output`),blendWithPrevious:!0}),this._outputPass.material.define(`fragment`,`OUTPUT_ALPHA`),this._outputPass.material.blend=function(e){e.blendEquationSeparate(e.FUNC_ADD,e.FUNC_ADD),e.blendFuncSeparate(e.ONE,e.ONE_MINUS_SRC_ALPHA,e.ONE,e.ONE_MINUS_SRC_ALPHA)}}ts.prototype={constructor:ts,jitterProjection:function(e,t){var n=e.viewport,r=n.devicePixelRatio||e.getDevicePixelRatio(),i=n.width*r,a=n.height*r,o=this._haltonSequence[this._frame%this._haltonSequence.length],s=new H;s.array[12]=(o[0]*2-1)/i,s.array[13]=(o[1]*2-1)/a,H.mul(t.projectionMatrix,s,t.projectionMatrix),H.invert(t.invProjectionMatrix,t.projectionMatrix)},resetFrame:function(){this._frame=0},getFrame:function(){return this._frame},getSourceFrameBuffer:function(){return this._sourceFb},getOutputTexture:function(){return this._outputTex},resize:function(e,t){this._prevFrameTex.width=e,this._prevFrameTex.height=t,this._outputTex.width=e,this._outputTex.height=t,this._sourceTex.width=e,this._sourceTex.height=t,this._prevFrameTex.dirty(),this._outputTex.dirty(),this._sourceTex.dirty()},isFinished:function(){return this._frame>=this._haltonSequence.length},render:function(e,t,n){var r=this._blendPass;this._frame===0?(r.setUniform(`weight1`,0),r.setUniform(`weight2`,1)):(r.setUniform(`weight1`,.9),r.setUniform(`weight2`,.1)),r.setUniform(`texture1`,this._prevFrameTex),r.setUniform(`texture2`,t||this._sourceTex),this._blendFb.attach(this._outputTex),this._blendFb.bind(e),r.render(e),this._blendFb.unbind(e),n||(this._outputPass.setUniform(`texture`,this._outputTex),this._outputPass.render(e));var i=this._prevFrameTex;this._prevFrameTex=this._outputTex,this._outputTex=i,this._frame++},dispose:function(e){this._sourceFb.dispose(e),this._blendFb.dispose(e),this._prevFrameTex.dispose(e),this._outputTex.dispose(e),this._sourceTex.dispose(e),this._outputPass.dispose(e),this._blendPass.dispose(e)}};function ns(e){e=e||`perspective`,this.layer=null,this.scene=new dr,this.rootNode=this.scene,this.viewport={x:0,y:0,width:0,height:0},this.setProjection(e),this._compositor=new $,this._temporalSS=new ts,this._shadowMapPass=new co;for(var t=[],n=0,r=0;r<30;r++){for(var i=[],a=0;a<6;a++)i.push(Vo(n,2)*4-2),i.push(Vo(n,3)*4-2),n++;t.push(i)}this._pcfKernels=t,this.scene.on(`beforerender`,function(e,t,n){this.needsTemporalSS()&&this._temporalSS.jitterProjection(e,n)},this)}ns.prototype.setProjection=function(e){var t=this.camera;t&&t.update(),e===`perspective`?this.camera instanceof _r||(this.camera=new _r,t&&this.camera.setLocalTransform(t.localTransform)):this.camera instanceof _i||(this.camera=new _i,t&&this.camera.setLocalTransform(t.localTransform)),this.camera.near=.1,this.camera.far=2e3},ns.prototype.setViewport=function(e,t,n,r,i){this.camera instanceof _r&&(this.camera.aspect=n/r),i=i||1,this.viewport.x=e,this.viewport.y=t,this.viewport.width=n,this.viewport.height=r,this.viewport.devicePixelRatio=i,this._compositor.resize(n*i,r*i),this._temporalSS.resize(n*i,r*i)},ns.prototype.containPoint=function(e,t){var n=this.viewport;return t=this.layer.renderer.getHeight()-t,e>=n.x&&t>=n.y&&e<=n.x+n.width&&t<=n.y+n.height};var rs=new G;ns.prototype.castRay=function(e,t,n){var r=this.layer.renderer,i=r.viewport;return r.viewport=this.viewport,r.screenToNDC(e,t,rs),this.camera.castRay(rs,n),r.viewport=i,n},ns.prototype.prepareRender=function(){this.scene.update(),this.camera.update(),this.scene.updateLights();var e=this.scene.updateRenderList(this.camera);this._needsSortProgressively=!1;for(var t=0;t<e.transparent.length;t++){var n=e.transparent[t].geometry;n.needsSortVerticesProgressively&&n.needsSortVerticesProgressively()&&(this._needsSortProgressively=!0),n.needsSortTrianglesProgressively&&n.needsSortTrianglesProgressively()&&(this._needsSortProgressively=!0)}this._frame=0,this._temporalSS.resetFrame()},ns.prototype.render=function(e,t){this._doRender(e,t,this._frame),this._frame++},ns.prototype.needsAccumulate=function(){return this.needsTemporalSS()||this._needsSortProgressively},ns.prototype.needsTemporalSS=function(){var e=this._enableTemporalSS;return e===`auto`&&(e=this._enablePostEffect),e},ns.prototype.hasDOF=function(){return this._enableDOF},ns.prototype.isAccumulateFinished=function(){return this.needsTemporalSS()?this._temporalSS.isFinished():this._frame>30},ns.prototype._doRender=function(e,t,n){var r=this.scene,i=this.camera;n=n||0,this._updateTransparent(e,r,i,n),t||(this._shadowMapPass.kernelPCF=this._pcfKernels[0],this._shadowMapPass.render(e,r,i,!0)),this._updateShadowPCFKernel(n);var a=e.clearColor;if(e.gl.clearColor(a[0],a[1],a[2],a[3]),this._enablePostEffect&&(this.needsTemporalSS()&&this._temporalSS.jitterProjection(e,i),this._compositor.updateNormal(e,r,i,this._temporalSS.getFrame())),this._updateSSAO(e,r,i,this._temporalSS.getFrame()),this._enablePostEffect){var o=this._compositor.getSourceFrameBuffer();o.bind(e),e.gl.clear(e.gl.DEPTH_BUFFER_BIT|e.gl.COLOR_BUFFER_BIT),e.render(r,i,!0,!0),o.unbind(e),this.needsTemporalSS()&&t?(this._compositor.composite(e,r,i,this._temporalSS.getSourceFrameBuffer(),this._temporalSS.getFrame()),e.setViewport(this.viewport),this._temporalSS.render(e)):(e.setViewport(this.viewport),this._compositor.composite(e,r,i,null,0))}else if(this.needsTemporalSS()&&t){var o=this._temporalSS.getSourceFrameBuffer();o.bind(e),e.saveClear(),e.clearBit=e.gl.DEPTH_BUFFER_BIT|e.gl.COLOR_BUFFER_BIT,e.render(r,i,!0,!0),e.restoreClear(),o.unbind(e),e.setViewport(this.viewport),this._temporalSS.render(e)}else e.setViewport(this.viewport),e.render(r,i,!0,!0)},ns.prototype._updateTransparent=function(e,t,n,r){for(var i=new L,a=new H,o=n.getWorldPosition(),s=t.getRenderList(n).transparent,c=0;c<s.length;c++){var l=s[c],u=l.geometry;H.invert(a,l.worldTransform),L.transformMat4(i,o,a),u.needsSortTriangles&&u.needsSortTriangles()&&u.doSortTriangles(i,r),u.needsSortVertices&&u.needsSortVertices()&&u.doSortVertices(i,r)}},ns.prototype._updateSSAO=function(e,t,n){var r=this._enableSSAO&&this._enablePostEffect;r&&this._compositor.updateSSAO(e,t,n,this._temporalSS.getFrame());for(var i=t.getRenderList(n),a=0;a<i.opaque.length;a++){var o=i.opaque[a];o.renderNormal&&o.material[r?`enableTexture`:`disableTexture`](`ssaoMap`),r&&o.material.set(`ssaoMap`,this._compositor.getSSAOTexture())}},ns.prototype._updateShadowPCFKernel=function(e){for(var t=this._pcfKernels[e%this._pcfKernels.length],n=this.scene.getRenderList(this.camera).opaque,r=0;r<n.length;r++)n[r].receiveShadow&&(n[r].material.set(`pcfKernel`,t),n[r].material.define(`fragment`,`PCF_KERNEL_SIZE`,t.length/2))},ns.prototype.dispose=function(e){this._compositor.dispose(e.gl),this._temporalSS.dispose(e.gl),this._shadowMapPass.dispose(e)},ns.prototype.setPostEffect=function(e,t){var n=this._compositor;this._enablePostEffect=e.get(`enable`);var r=e.getModel(`bloom`),i=e.getModel(`edge`),a=e.getModel(`DOF`,e.getModel(`depthOfField`)),o=e.getModel(`SSAO`,e.getModel(`screenSpaceAmbientOcclusion`)),s=e.getModel(`SSR`,e.getModel(`screenSpaceReflection`)),c=e.getModel(`FXAA`),l=e.getModel(`colorCorrection`);r.get(`enable`)?n.enableBloom():n.disableBloom(),a.get(`enable`)?n.enableDOF():n.disableDOF(),s.get(`enable`)?n.enableSSR():n.disableSSR(),l.get(`enable`)?n.enableColorCorrection():n.disableColorCorrection(),i.get(`enable`)?n.enableEdge():n.disableEdge(),c.get(`enable`)?n.enableFXAA():n.disableFXAA(),this._enableDOF=a.get(`enable`),this._enableSSAO=o.get(`enable`),this._enableSSAO?n.enableSSAO():n.disableSSAO(),n.setBloomIntensity(r.get(`intensity`)),n.setEdgeColor(i.get(`color`)),n.setColorLookupTexture(l.get(`lookupTexture`),t),n.setExposure(l.get(`exposure`)),[`radius`,`quality`,`intensity`].forEach(function(e){n.setSSAOParameter(e,o.get(e))}),[`quality`,`maxRoughness`,`physical`].forEach(function(e){n.setSSRParameter(e,s.get(e))}),[`quality`,`focalDistance`,`focalRange`,`blurRadius`,`fstop`].forEach(function(e){n.setDOFParameter(e,a.get(e))}),[`brightness`,`contrast`,`saturation`].forEach(function(e){n.setColorCorrection(e,l.get(e))})},ns.prototype.setDOFFocusOnPoint=function(e){if(this._enablePostEffect)return e>this.camera.far||e<this.camera.near?void 0:(this._compositor.setDOFParameter(`focalDistance`,e),!0)},ns.prototype.setTemporalSuperSampling=function(e){this._enableTemporalSS=e.get(`enable`)},ns.prototype.isLinearSpace=function(){return this._enablePostEffect},ns.prototype.setRootNode=function(e){if(this.rootNode!==e){for(var t=this.rootNode.children(),n=0;n<t.length;n++)e.add(t[n]);e!==this.scene&&this.scene.add(e),this.rootNode=e}},ns.prototype.add=function(e){this.rootNode.add(e)},ns.prototype.remove=function(e){this.rootNode.remove(e)},ns.prototype.removeAll=function(e){this.rootNode.removeAll(e)},Object.assign(ns.prototype,je);function is(e,t){var n=E(e.getBoxLayoutParams(),{width:t.getWidth(),height:t.getHeight()});n.y=t.getHeight()-n.y-n.height,this.viewGL.setViewport(n.x,n.y,n.width,n.height,t.getDevicePixelRatio());var r=e.get(`boxWidth`),i=e.get(`boxHeight`),a=e.get(`boxDepth`);this.getAxis(`x`).setExtent(-r/2,r/2),this.getAxis(`y`).setExtent(a/2,-a/2),this.getAxis(`z`).setExtent(-i/2,i/2),this.size=[r,i,a]}function as(e,t){var n={};function r(e,t){n[e]=n[e]||[1/0,-1/0],n[e][0]=Math.min(t[0],n[e][0]),n[e][1]=Math.max(t[1],n[e][1])}e.eachSeries(function(e){if(e.coordinateSystem===this){var t=e.getData();[`x`,`y`,`z`].forEach(function(e){t.mapDimensionsAll(e,!0).forEach(function(n){r(e,t.getDataExtent(n,!0))})})}},this),[`xAxis3D`,`yAxis3D`,`zAxis3D`].forEach(function(t){e.eachComponent(t,function(e){var r=t.charAt(0),i=e.getReferringComponents(`grid3D`).models[0],a=i.coordinateSystem;if(a===this){var s=a.getAxis(r);if(!s){s=new Za(r,o(n[r]||[1/0,-1/0],e)),s.type=e.get(`type`);var c=s.type===`category`;s.onBand=c&&e.get(`boundaryGap`),s.inverse=e.get(`inverse`),e.axis=s,s.model=e,s.getLabelModel=function(){return e.getModel(`axisLabel`,i.getModel(`axisLabel`))},s.getTickModel=function(){return e.getModel(`axisTick`,i.getModel(`axisTick`))},a.addAxis(s)}}},this)},this),this.resize(this.model,t)}var os={dimensions:Xa.prototype.dimensions,create:function(e,t){var n=[];e.eachComponent(`grid3D`,function(e){e.__viewGL=e.__viewGL||new ns;var t=new Xa;t.model=e,t.viewGL=e.__viewGL,e.coordinateSystem=t,n.push(t),t.resize=is,t.update=as});var r=[`xAxis3D`,`yAxis3D`,`zAxis3D`];function i(e,t){return r.map(function(n){var r=e.getReferringComponents(n).models[0];return r==null&&(r=t.getComponent(n)),r})}return e.eachSeries(function(t){if(t.get(`coordinateSystem`)===`cartesian3D`){var n=t.getReferringComponents(`grid3D`).models[0];if(n==null){var r=i(t,e),n=r[0].getCoordSysModel();r.forEach(function(e){e.getCoordSysModel()})}t.coordinateSystem=n.coordinateSystem}}),n}},ss=D.extend({type:`cartesian3DAxis`,axis:null,getCoordSysModel:function(){return this.ecModel.queryComponents({mainType:`grid3D`,index:this.option.gridIndex,id:this.option.gridId})[0]}});f(ss);var cs={show:!0,grid3DIndex:0,inverse:!1,name:``,nameLocation:`middle`,nameTextStyle:{fontSize:16},nameGap:20,axisPointer:{},axisLine:{},axisTick:{},axisLabel:{},splitArea:{}},ls=m({boundaryGap:!0,axisTick:{alignWithLabel:!1,interval:`auto`},axisLabel:{interval:`auto`},axisPointer:{label:{show:!1}}},cs),us=m({boundaryGap:[0,0],splitNumber:5,axisPointer:{label:{}}},cs),ds=C({scale:!0,min:`dataMin`,max:`dataMax`},us),fs=C({logBase:10},us);fs.scale=!0;var ps={categoryAxis3D:ls,valueAxis3D:us,timeAxis3D:ds,logAxis3D:fs},ms=[`value`,`category`,`time`,`log`];function hs(e,t,n,r,i){ms.forEach(function(a){var o=n.extend({type:t+`Axis3D.`+a,__ordinalMeta:null,mergeDefaultAndTheme:function(e,n){m(e,n.getTheme().get(a+`Axis3D`)),m(e,this.getDefaultOption()),e.type=r(t,e)},optionUpdated:function(){this.option.type===`category`&&(this.__ordinalMeta=b.createByAxisModel(this))},getCategories:function(){if(this.option.type===`category`)return this.__ordinalMeta.categories},getOrdinalMeta:function(){return this.__ordinalMeta},defaultOption:m(x(ps[a+`Axis3D`]),i||{},!0)});e.registerComponentModel(o)}),e.registerSubTypeDefaulter(t+`Axis3D`,xe(r,t))}function gs(e,t){return t.type||(t.data?`category`:`value`)}function _s(e){e.registerComponentModel(ba),e.registerComponentView(Ya),e.registerCoordinateSystem(`grid3D`,os),[`x`,`y`,`z`].forEach(function(t){hs(e,t,ss,gs,{name:t.toUpperCase()});let n=e.ComponentView.extend({type:t+`Axis3D`});e.registerComponentView(n)}),e.registerAction({type:`grid3DChangeCamera`,event:`grid3dcamerachanged`,update:`series:updateCamera`},function(e,t){t.eachComponent({mainType:`grid3D`,query:e},function(t){t.setView(e)})}),e.registerAction({type:`grid3DShowAxisPointer`,event:`grid3dshowaxispointer`,update:`grid3D:showAxisPointer`},function(e,t){}),e.registerAction({type:`grid3DHideAxisPointer`,event:`grid3dhideaxispointer`,update:`grid3D:hideAxisPointer`},function(e,t){})}h(_s);var vs={defaultOption:{shading:null,realisticMaterial:{textureTiling:1,textureOffset:0,detailTexture:null},lambertMaterial:{textureTiling:1,textureOffset:0,detailTexture:null},colorMaterial:{textureTiling:1,textureOffset:0,detailTexture:null},hatchingMaterial:{textureTiling:1,textureOffset:0,paperColor:`#fff`}}},ys={getFilledRegions:function(e,t){var n=(e||[]).slice(),r;if(typeof t==`string`?(t=c(t),r=t&&t.geoJson):t&&t.features&&(r=t),!r)return[];for(var i={},a=r.features,o=0;o<n.length;o++)i[n[o].name]=n[o];for(var o=0;o<a.length;o++){var s=a[o].properties.name;i[s]||n.push({name:s})}return n},defaultOption:{show:!0,zlevel:-10,map:``,left:0,top:0,width:`100%`,height:`100%`,boxWidth:100,boxHeight:10,boxDepth:`auto`,regionHeight:3,environment:`auto`,groundPlane:{show:!1,color:`#aaa`},shading:`lambert`,light:{main:{alpha:40,beta:30}},viewControl:{alpha:40,beta:0,distance:100,orthographicSize:60,minAlpha:5,minBeta:-80,maxBeta:80},label:{show:!1,distance:2,textStyle:{fontSize:20,color:`#000`,backgroundColor:`rgba(255,255,255,0.7)`,padding:3,borderRadius:4}},itemStyle:{color:`#fff`,borderWidth:0,borderColor:`#333`},emphasis:{itemStyle:{color:`#639fc0`},label:{show:!0}}}},bs=D.extend({type:`geo3D`,layoutMode:`box`,coordinateSystem:null,optionUpdated:function(){var e=this.option;e.regions=this.getFilledRegions(e.regions,e.map);var t=new n(Te(e.data||[],{coordDimensions:[`value`],encodeDefine:this.get(`encode`),dimensionsDefine:this.get(`dimensions`)}),this);t.initData(e.regions);var r={};t.each(function(e){var n=t.getName(e);r[n]=t.getItemModel(e)}),this._regionModelMap=r,this._data=t},getData:function(){return this._data},getRegionModel:function(e){var t=this.getData().getName(e);return this._regionModelMap[t]||new _e(null,this)},getRegionPolygonCoords:function(e){var t=this.getData().getName(e),n=this.coordinateSystem.getRegion(t);return n?n.geometries:[]},getFormattedLabel:function(e,t){var n=this._data.getName(e),r=this.getRegionModel(e),i=r.get(t===`normal`?[`label`,`formatter`]:[`emphasis`,`label`,`formatter`]);i==null&&(i=r.get([`label`,`formatter`]));var a={name:n};if(typeof i==`function`)return a.status=t,i(a);if(typeof i==`string`){var o=a.seriesName;return i.replace(`{a}`,o==null?``:o)}else return n},defaultOption:{regions:[]}});m(bs.prototype,ys),m(bs.prototype,_a),m(bs.prototype,va),m(bs.prototype,ya),m(bs.prototype,vs);var xs=Ss;function Ss(e,t,n){n=n||2;var r=t&&t.length,i=r?t[0]*n:e.length,a=Cs(e,0,i,n,!0),o=[];if(!a)return o;var s,c,l,u,d,f,p;if(r&&(a=As(e,t,a,n)),e.length>80*n){s=l=e[0],c=u=e[1];for(var m=n;m<i;m+=n)d=e[m],f=e[m+1],d<s&&(s=d),f<c&&(c=f),d>l&&(l=d),f>u&&(u=f);p=Math.max(l-s,u-c)}return Ts(a,o,n,s,c,p),o}function Cs(e,t,n,r,i){var a,o;if(i===Xs(e,t,n,r)>0)for(a=t;a<n;a+=r)o=qs(a,e[a],e[a+1],o);else for(a=n-r;a>=t;a-=r)o=qs(a,e[a],e[a+1],o);return o&&Vs(o,o.next)&&(Js(o),o=o.next),o}function ws(e,t){if(!e)return e;t||(t=e);var n=e,r;do if(r=!1,!n.steiner&&(Vs(n,n.next)||Bs(n.prev,n,n.next)===0)){if(Js(n),n=t=n.prev,n===n.next)return null;r=!0}else n=n.next;while(r||n!==t);return t}function Ts(e,t,n,r,i,a,o){if(e){!o&&a&&Ps(e,r,i,a);for(var s=e,c,l;e.prev!==e.next;){if(c=e.prev,l=e.next,a?Ds(e,r,i,a):Es(e)){t.push(c.i/n),t.push(e.i/n),t.push(l.i/n),Js(e),e=l.next,s=l.next;continue}if(e=l,e===s){o?o===1?(e=Os(e,t,n),Ts(e,t,n,r,i,a,2)):o===2&&ks(e,t,n,r,i,a):Ts(ws(e),t,n,r,i,a,1);break}}}}function Es(e){var t=e.prev,n=e,r=e.next;if(Bs(t,n,r)>=0)return!1;for(var i=e.next.next;i!==e.prev;){if(Rs(t.x,t.y,n.x,n.y,r.x,r.y,i.x,i.y)&&Bs(i.prev,i,i.next)>=0)return!1;i=i.next}return!0}function Ds(e,t,n,r){var i=e.prev,a=e,o=e.next;if(Bs(i,a,o)>=0)return!1;for(var s=i.x<a.x?i.x<o.x?i.x:o.x:a.x<o.x?a.x:o.x,c=i.y<a.y?i.y<o.y?i.y:o.y:a.y<o.y?a.y:o.y,l=i.x>a.x?i.x>o.x?i.x:o.x:a.x>o.x?a.x:o.x,u=i.y>a.y?i.y>o.y?i.y:o.y:a.y>o.y?a.y:o.y,d=Is(s,c,t,n,r),f=Is(l,u,t,n,r),p=e.nextZ;p&&p.z<=f;){if(p!==e.prev&&p!==e.next&&Rs(i.x,i.y,a.x,a.y,o.x,o.y,p.x,p.y)&&Bs(p.prev,p,p.next)>=0)return!1;p=p.nextZ}for(p=e.prevZ;p&&p.z>=d;){if(p!==e.prev&&p!==e.next&&Rs(i.x,i.y,a.x,a.y,o.x,o.y,p.x,p.y)&&Bs(p.prev,p,p.next)>=0)return!1;p=p.prevZ}return!0}function Os(e,t,n){var r=e;do{var i=r.prev,a=r.next.next;!Vs(i,a)&&Hs(i,r,r.next,a)&&Ws(i,a)&&Ws(a,i)&&(t.push(i.i/n),t.push(r.i/n),t.push(a.i/n),Js(r),Js(r.next),r=e=a),r=r.next}while(r!==e);return r}function ks(e,t,n,r,i,a){var o=e;do{for(var s=o.next.next;s!==o.prev;){if(o.i!==s.i&&zs(o,s)){var c=Ks(o,s);o=ws(o,o.next),c=ws(c,c.next),Ts(o,t,n,r,i,a),Ts(c,t,n,r,i,a);return}s=s.next}o=o.next}while(o!==e)}function As(e,t,n,r){var i=[],a,o,s,c,l;for(a=0,o=t.length;a<o;a++)s=t[a]*r,c=a<o-1?t[a+1]*r:e.length,l=Cs(e,s,c,r,!1),l===l.next&&(l.steiner=!0),i.push(Ls(l));for(i.sort(js),a=0;a<i.length;a++)Ms(i[a],n),n=ws(n,n.next);return n}function js(e,t){return e.x-t.x}function Ms(e,t){if(t=Ns(e,t),t){var n=Ks(t,e);ws(n,n.next)}}function Ns(e,t){var n=t,r=e.x,i=e.y,a=-1/0,o;do{if(i<=n.y&&i>=n.next.y&&n.next.y!==n.y){var s=n.x+(i-n.y)*(n.next.x-n.x)/(n.next.y-n.y);if(s<=r&&s>a){if(a=s,s===r){if(i===n.y)return n;if(i===n.next.y)return n.next}o=n.x<n.next.x?n:n.next}}n=n.next}while(n!==t);if(!o)return null;if(r===a)return o.prev;var c=o,l=o.x,u=o.y,d=1/0,f;for(n=o.next;n!==c;)r>=n.x&&n.x>=l&&r!==n.x&&Rs(i<u?r:a,i,l,u,i<u?a:r,i,n.x,n.y)&&(f=Math.abs(i-n.y)/(r-n.x),(f<d||f===d&&n.x>o.x)&&Ws(n,e)&&(o=n,d=f)),n=n.next;return o}function Ps(e,t,n,r){var i=e;do i.z===null&&(i.z=Is(i.x,i.y,t,n,r)),i.prevZ=i.prev,i.nextZ=i.next,i=i.next;while(i!==e);i.prevZ.nextZ=null,i.prevZ=null,Fs(i)}function Fs(e){var t,n,r,i,a,o,s,c,l=1;do{for(n=e,e=null,a=null,o=0;n;){for(o++,r=n,s=0,t=0;t<l&&(s++,r=r.nextZ,r);t++);for(c=l;s>0||c>0&&r;)s!==0&&(c===0||!r||n.z<=r.z)?(i=n,n=n.nextZ,s--):(i=r,r=r.nextZ,c--),a?a.nextZ=i:e=i,i.prevZ=a,a=i;n=r}a.nextZ=null,l*=2}while(o>1);return e}function Is(e,t,n,r,i){return e=32767*(e-n)/i,t=32767*(t-r)/i,e=(e|e<<8)&16711935,e=(e|e<<4)&252645135,e=(e|e<<2)&858993459,e=(e|e<<1)&1431655765,t=(t|t<<8)&16711935,t=(t|t<<4)&252645135,t=(t|t<<2)&858993459,t=(t|t<<1)&1431655765,e|t<<1}function Ls(e){var t=e,n=e;do t.x<n.x&&(n=t),t=t.next;while(t!==e);return n}function Rs(e,t,n,r,i,a,o,s){return(i-o)*(t-s)-(e-o)*(a-s)>=0&&(e-o)*(r-s)-(n-o)*(t-s)>=0&&(n-o)*(a-s)-(i-o)*(r-s)>=0}function zs(e,t){return e.next.i!==t.i&&e.prev.i!==t.i&&!Us(e,t)&&Ws(e,t)&&Ws(t,e)&&Gs(e,t)}function Bs(e,t,n){return(t.y-e.y)*(n.x-t.x)-(t.x-e.x)*(n.y-t.y)}function Vs(e,t){return e.x===t.x&&e.y===t.y}function Hs(e,t,n,r){return Vs(e,t)&&Vs(n,r)||Vs(e,r)&&Vs(n,t)?!0:Bs(e,t,n)>0!=Bs(e,t,r)>0&&Bs(n,r,e)>0!=Bs(n,r,t)>0}function Us(e,t){var n=e;do{if(n.i!==e.i&&n.next.i!==e.i&&n.i!==t.i&&n.next.i!==t.i&&Hs(n,n.next,e,t))return!0;n=n.next}while(n!==e);return!1}function Ws(e,t){return Bs(e.prev,e,e.next)<0?Bs(e,t,e.next)>=0&&Bs(e,e.prev,t)>=0:Bs(e,t,e.prev)<0||Bs(e,e.next,t)<0}function Gs(e,t){var n=e,r=!1,i=(e.x+t.x)/2,a=(e.y+t.y)/2;do n.y>a!=n.next.y>a&&n.next.y!==n.y&&i<(n.next.x-n.x)*(a-n.y)/(n.next.y-n.y)+n.x&&(r=!r),n=n.next;while(n!==e);return r}function Ks(e,t){var n=new Ys(e.i,e.x,e.y),r=new Ys(t.i,t.x,t.y),i=e.next,a=t.prev;return e.next=t,t.prev=e,n.next=i,i.prev=n,r.next=n,n.prev=r,a.next=r,r.prev=a,r}function qs(e,t,n,r){var i=new Ys(e,t,n);return r?(i.next=r.next,i.prev=r,r.next.prev=i,r.next=i):(i.prev=i,i.next=i),i}function Js(e){e.next.prev=e.prev,e.prev.next=e.next,e.prevZ&&(e.prevZ.nextZ=e.nextZ),e.nextZ&&(e.nextZ.prevZ=e.prevZ)}function Ys(e,t,n){this.i=e,this.x=t,this.y=n,this.prev=null,this.next=null,this.z=null,this.prevZ=null,this.nextZ=null,this.steiner=!1}Ss.deviation=function(e,t,n,r){var i=t&&t.length,a=i?t[0]*n:e.length,o=Math.abs(Xs(e,0,a,n));if(i)for(var s=0,c=t.length;s<c;s++){var l=t[s]*n,u=s<c-1?t[s+1]*n:e.length;o-=Math.abs(Xs(e,l,u,n))}var d=0;for(s=0;s<r.length;s+=3){var f=r[s]*n,p=r[s+1]*n,m=r[s+2]*n;d+=Math.abs((e[f]-e[m])*(e[p+1]-e[f+1])-(e[f]-e[p])*(e[m+1]-e[f+1]))}return o===0&&d===0?0:Math.abs((d-o)/o)};function Xs(e,t,n,r){for(var i=0,a=t,o=n-r;a<n;a+=r)i+=(e[o]-e[a])*(e[a+1]+e[o+1]),o=a;return i}function Zs(e,t,n){var r=e[t];e[t]=e[n],e[n]=r}function Qs(e,t,n,r,i){var a=n,o=e[t];Zs(e,t,r);for(var s=n;s<r;s++)i(e[s],o)<0&&(Zs(e,s,a),a++);return Zs(e,r,a),a}function $s(e,t,n,r){if(n<r){var i=Qs(e,Math.floor((n+r)/2),n,r,t);$s(e,t,n,i-1),$s(e,t,i+1,r)}}function ec(){this._parts=[]}ec.prototype.step=function(e,t,n){var r=e.length;if(n===0){this._parts=[],this._sorted=!1;var i=Math.floor(r/2);this._parts.push({pivot:i,left:0,right:r-1}),this._currentSortPartIdx=0}if(!this._sorted){var a=this._parts;if(a.length===0)return this._sorted=!0,!0;if(a.length<512){for(var o=0;o<a.length;o++)a[o].pivot=Qs(e,a[o].pivot,a[o].left,a[o].right,t);for(var s=[],o=0;o<a.length;o++){var c=a[o].left,l=a[o].pivot-1;l>c&&s.push({pivot:Math.floor((l+c)/2),left:c,right:l});var c=a[o].pivot+1,l=a[o].right;l>c&&s.push({pivot:Math.floor((l+c)/2),left:c,right:l})}a=this._parts=s}else for(var o=0;o<Math.floor(a.length/10);o++){var u=a.length-1-this._currentSortPartIdx;if($s(e,t,a[u].left,a[u].right),this._currentSortPartIdx++,this._currentSortPartIdx===a.length)return this._sorted=!0,!0}return!1}},ec.sort=$s;var tc=Ea.vec3,nc=tc.create(),rc=tc.create(),ic=tc.create(),ac={needsSortTriangles:function(){return this.indices&&this.sortTriangles},needsSortTrianglesProgressively:function(){return this.needsSortTriangles()&&this.triangleCount>=2e4},doSortTriangles:function(e,t){var n=this.indices;if(t===0){var r=this.attributes.position,e=e.array;(!this._triangleZList||this._triangleZList.length!==this.triangleCount)&&(this._triangleZList=new Float32Array(this.triangleCount),this._sortedTriangleIndices=new Uint32Array(this.triangleCount),this._indicesTmp=new n.constructor(n.length),this._triangleZListTmp=new Float32Array(this.triangleCount));for(var i=0,a,o=0;o<n.length;){r.get(n[o++],nc),r.get(n[o++],rc),r.get(n[o++],ic);var s=tc.sqrDist(nc,e),c=tc.sqrDist(rc,e),l=tc.sqrDist(ic,e),u=Math.min(s,c);u=Math.min(u,l),o===3?(a=u,u=0):u-=a,this._triangleZList[i++]=u}}for(var d=this._sortedTriangleIndices,o=0;o<d.length;o++)d[o]=o;if(this.triangleCount<2e4)t===0&&this._simpleSort(!0);else for(var o=0;o<3;o++)this._progressiveQuickSort(t*3+o);for(var f=this._indicesTmp,p=this._triangleZListTmp,m=this._triangleZList,o=0;o<this.triangleCount;o++){var h=d[o]*3,g=o*3;f[g++]=n[h++],f[g++]=n[h++],f[g]=n[h],p[o]=m[d[o]]}var _=this._indicesTmp;this._indicesTmp=this.indices,this.indices=_;var _=this._triangleZListTmp;this._triangleZListTmp=this._triangleZList,this._triangleZList=_,this.dirtyIndices()},_simpleSort:function(e){var t=this._triangleZList,n=this._sortedTriangleIndices;function r(e,n){return t[n]-t[e]}e?Array.prototype.sort.call(n,r):ec.sort(n,r,0,n.length-1)},_progressiveQuickSort:function(e){var t=this._triangleZList,n=this._sortedTriangleIndices;this._quickSort=this._quickSort||new ec,this._quickSort.step(n,function(e,n){return t[n]-t[e]},e)}};function oc(e){let t=e.getVisual(`style`);if(t)return t[e.getVisual(`drawType`)]}function sc(e){return e.getVisual(`style`).opacity}function cc(e,t){let n=e.getItemVisual(t,`style`);if(n)return n[e.getVisual(`drawType`)]}function lc(e,t){let n=e.getItemVisual(t,`style`);return n&&n.opacity}var uc=1,dc=2;function fc(e,t,n){this._labelsMesh=new Va,this._labelTextureSurface=new ja({width:512,height:512,devicePixelRatio:n.getDevicePixelRatio(),onupdate:function(){n.getZr().refresh()}}),this._api=n,this._labelsMesh.material.set(`textureAtlas`,this._labelTextureSurface.getTexture())}fc.prototype.getLabelPosition=function(e,t,n){return[0,0,0]},fc.prototype.getLabelDistance=function(e,t,n){return 0},fc.prototype.getMesh=function(){return this._labelsMesh},fc.prototype.updateData=function(e,t,n){t==null&&(t=0),n==null&&(n=e.count()),(!this._labelsVisibilitiesBits||this._labelsVisibilitiesBits.length!==n-t)&&(this._labelsVisibilitiesBits=new Uint8Array(n-t));for(var r=[`label`,`show`],i=[`emphasis`,`label`,`show`],a=t;a<n;a++){var o=e.getItemModel(a),s=o.get(r),c=o.get(i);c==null&&(c=s);var l=(s?uc:0)|(c?dc:0);this._labelsVisibilitiesBits[a-t]=l}this._start=t,this._end=n,this._data=e},fc.prototype.updateLabels=function(e){if(this._data){e=e||[];for(var t=e.length>0,n={},r=0;r<e.length;r++)n[e[r]]=!0;this._labelsMesh.geometry.convertToDynamicArray(!0),this._labelTextureSurface.clear();for(var i=[`label`],a=[`emphasis`,`label`],o=this._data.hostModel,s=this._data,c=o.getModel(i),l=o.getModel(a,c),u={left:`right`,right:`left`,top:`center`,bottom:`center`},d={left:`middle`,right:`middle`,top:`bottom`,bottom:`top`},f=this._start;f<this._end;f++){var p=!1;if(t&&n[f]&&(p=!0),this._labelsVisibilitiesBits[f-this._start]&(p?dc:uc)){var m=s.getItemModel(f).getModel(p?a:i,p?l:c),h=m.get(`distance`)||0,g=m.get(`position`),_=this._api.getDevicePixelRatio(),v=o.getFormattedLabel(f,p?`emphasis`:`normal`);if(v==null||v===``)return;var y=new re({style:le(m,{text:v,fill:m.get(`color`)||cc(s,f)||`#000`,align:`left`,verticalAlign:`top`,opacity:X.firstNotNull(m.get(`opacity`),lc(s,f),1)})}),b=y.getBoundingRect();b.height*=1.2;var x=this._labelTextureSurface.add(y),S=u[g]||`center`,C=d[g]||`bottom`;this._labelsMesh.geometry.addSprite(this.getLabelPosition(f,g,h),[b.width*_,b.height*_],x,S,C,this.getLabelDistance(f,g,h)*_)}}this._labelsMesh.material.set(`uvScale`,this._labelTextureSurface.getCoordsScale()),this._labelTextureSurface.getZr().refreshImmediately(),this._labelsMesh.geometry.convertToTypedArray(),this._labelsMesh.geometry.dirty()}},fc.prototype.dispose=function(){this._labelTextureSurface.dispose()};var pc=Ea.vec3;Q.Shader.import(Ka);function mc(e){this.rootNode=new Q.Node,this._triangulationResults={},this._shadersMap=Q.COMMON_SHADERS.filter(function(e){return e!==`shadow`}).reduce(function(e,t){return e[t]=Q.createShader(`ecgl.`+t),e},{}),this._linesShader=Q.createShader(`ecgl.meshLines3D`);var t={};Q.COMMON_SHADERS.forEach(function(e){t[e]=new Q.Material({shader:Q.createShader(`ecgl.`+e)})}),this._groundMaterials=t,this._groundMesh=new Q.Mesh({geometry:new Q.PlaneGeometry({dynamic:!0}),castShadow:!1,renderNormal:!0,$ignorePicking:!0}),this._groundMesh.rotation.rotateX(-Math.PI/2),this._labelsBuilder=new fc(512,512,e),this._labelsBuilder.getMesh().renderOrder=100,this._labelsBuilder.getMesh().material.depthTest=!1,this.rootNode.add(this._labelsBuilder.getMesh()),this._initMeshes(),this._api=e}mc.prototype={constructor:mc,extrudeY:!0,update:function(e,t,n,r,i){var a=e.getData();r==null&&(r=0),i==null&&(i=a.count()),this._startIndex=r,this._endIndex=i-1,this._triangulation(e,r,i);var o=this._getShader(e.get(`shading`));this._prepareMesh(e,o,n,r,i),this.rootNode.updateWorldTransform(),this._updateRegionMesh(e,n,r,i);var s=e.coordinateSystem;s.type===`geo3D`&&this._updateGroundPlane(e,s,n);var c=this;this._labelsBuilder.updateData(a,r,i),this._labelsBuilder.getLabelPosition=function(e,t,n){var r=a.getName(e),i,o=n;if(s.type===`geo3D`){var l=s.getRegion(r);return l?(i=l.getCenter(),s.dataToPoint([i[0],i[1],o])):[NaN,NaN,NaN]}else var u=c._triangulationResults[e-c._startIndex],i=c.extrudeY?[(u.max[0]+u.min[0])/2,u.max[1]+o,(u.max[2]+u.min[2])/2]:[(u.max[0]+u.min[0])/2,(u.max[1]+u.min[1])/2,u.max[2]+o]},this._data=a,this._labelsBuilder.updateLabels(),this._updateDebugWireframe(e),this._lastHoverDataIndex=0},_initMeshes:function(){var e=this;function t(){var t=new Q.Mesh({name:`Polygon`,material:new Q.Material({shader:e._shadersMap.lambert}),geometry:new Q.Geometry({sortTriangles:!0,dynamic:!0}),culling:!1,ignorePicking:!0,renderNormal:!0});return Object.assign(t.geometry,ac),t}var n=t(),r=new Q.Mesh({material:new Q.Material({shader:this._linesShader}),castShadow:!1,ignorePicking:!0,$ignorePicking:!0,geometry:new ka({useNativeLine:!1})});this.rootNode.add(n),this.rootNode.add(r),n.material.define(`both`,`VERTEX_COLOR`),n.material.define(`fragment`,`DOUBLE_SIDED`),this._polygonMesh=n,this._linesMesh=r,this.rootNode.add(this._groundMesh)},_getShader:function(e){var t=this._shadersMap[e];return t||(t=this._shadersMap.lambert),t.__shading=e,t},_prepareMesh:function(e,t,n,r,i){for(var a=0,o=0,s=0,c=0,l=r;l<i;l++){var u=this._getRegionPolygonInfo(l),d=this._getRegionLinesInfo(l,e,this._linesMesh.geometry);a+=u.vertexCount,o+=u.triangleCount,s+=d.vertexCount,c+=d.triangleCount}var f=this._polygonMesh,p=f.geometry;[`position`,`normal`,`texcoord0`,`color`].forEach(function(e){p.attributes[e].init(a)}),p.indices=a>65535?new Uint32Array(o*3):new Uint16Array(o*3),f.material.shader!==t&&f.material.attachShader(t,!0),Q.setMaterialFromModel(t.__shading,f.material,e,n),s>0&&(this._linesMesh.geometry.resetOffset(),this._linesMesh.geometry.setVertexCount(s),this._linesMesh.geometry.setTriangleCount(c)),this._dataIndexOfVertex=new Uint32Array(a),this._vertexRangeOfDataIndex=new Uint32Array((i-r)*2)},_updateRegionMesh:function(e,t,n,r){for(var i=e.getData(),a=0,o=0,s=!1,c=this._polygonMesh,l=this._linesMesh,u=n;u<r;u++){var d=e.getRegionModel(u),f=d.getModel(`itemStyle`),p=X.firstNotNull(cc(i,u),f.get(`color`),`#fff`),m=X.firstNotNull(lc(i,u),f.get(`opacity`),1),h=Q.parseColor(p),g=Q.parseColor(f.get(`borderColor`));h[3]*=m,g[3]*=m;var _=h[3]<.99;c.material.set(`color`,[1,1,1,1]),s=s||_;for(var v=X.firstNotNull(d.get(`height`,!0),e.get(`regionHeight`)),y=this._updatePolygonGeometry(e,c.geometry,u,v,a,o,h),b=a;b<y.vertexOffset;b++)this._dataIndexOfVertex[b]=u;this._vertexRangeOfDataIndex[(u-n)*2]=a,this._vertexRangeOfDataIndex[(u-n)*2+1]=y.vertexOffset,a=y.vertexOffset,o=y.triangleOffset;var x=f.get(`borderWidth`),S=x>0;S&&(x*=t.getDevicePixelRatio(),this._updateLinesGeometry(l.geometry,e,u,v,x,e.coordinateSystem.transform)),l.invisible=!S,l.material.set({color:g})}var c=this._polygonMesh;c.material.transparent=s,c.material.depthMask=!s,c.geometry.updateBoundingBox(),c.frontFace=this.extrudeY?Q.Mesh.CCW:Q.Mesh.CW,c.material.get(`normalMap`)&&c.geometry.generateTangents(),c.seriesIndex=e.seriesIndex,c.on(`mousemove`,this._onmousemove,this),c.on(`mouseout`,this._onmouseout,this)},_updateDebugWireframe:function(e){var t=e.getModel(`debug.wireframe`);if(t.get(`show`)){var n=Q.parseColor(t.get(`lineStyle.color`)||`rgba(0,0,0,0.5)`),r=X.firstNotNull(t.get(`lineStyle.width`),1),i=this._polygonMesh;i.geometry.generateBarycentric(),i.material.define(`both`,`WIREFRAME_TRIANGLE`),i.material.set(`wireframeLineColor`,n),i.material.set(`wireframeLineWidth`,r)}},_onmousemove:function(e){var t=this._dataIndexOfVertex[e.triangle[0]];t==null&&(t=-1),t!==this._lastHoverDataIndex&&(this.downplay(this._lastHoverDataIndex),this.highlight(t),this._labelsBuilder.updateLabels([t])),this._lastHoverDataIndex=t,this._polygonMesh.dataIndex=t},_onmouseout:function(e){e.target&&(this.downplay(this._lastHoverDataIndex),this._lastHoverDataIndex=-1,this._polygonMesh.dataIndex=-1),this._labelsBuilder.updateLabels([])},_updateGroundPlane:function(e,t,n){var r=e.getModel(`groundPlane`,e);if(this._groundMesh.invisible=!r.get(`show`,!0),!this._groundMesh.invisible){var i=e.get(`shading`),a=this._groundMaterials[i];a||(a=this._groundMaterials.lambert),Q.setMaterialFromModel(i,a,r,n),a.get(`normalMap`)&&this._groundMesh.geometry.generateTangents(),this._groundMesh.material=a,this._groundMesh.material.set(`color`,Q.parseColor(r.get(`color`))),this._groundMesh.scale.set(t.size[0],t.size[2],1)}},_triangulation:function(e,t,n){this._triangulationResults=[];for(var r=[1/0,1/0,1/0],i=[-1/0,-1/0,-1/0],a=e.coordinateSystem,o=t;o<n;o++){for(var s=[],c=e.getRegionPolygonCoords(o),l=0;l<c.length;l++){var u=c[l].exterior,d=c[l].interiors,f=[],p=[];if(!(u.length<3)){for(var m=0,h=0;h<u.length;h++){var g=u[h];f[m++]=g[0],f[m++]=g[1]}for(var h=0;h<d.length;h++)if(!(d[h].length<3)){for(var _=f.length/2,v=0;v<d[h].length;v++){var g=d[h][v];f.push(g[0]),f.push(g[1])}p.push(_)}for(var y=xs(f,p),b=new Float64Array(f.length/2*3),x=[],S=[1/0,1/0,1/0],C=[-1/0,-1/0,-1/0],w=0,h=0;h<f.length;)pc.set(x,f[h++],0,f[h++]),a&&a.transform&&pc.transformMat4(x,x,a.transform),pc.min(S,S,x),pc.max(C,C,x),b[w++]=x[0],b[w++]=x[1],b[w++]=x[2];pc.min(r,r,S),pc.max(i,i,C),s.push({points:b,indices:y,min:S,max:C})}}this._triangulationResults.push(s)}this._geoBoundingBox=[r,i]},_getRegionPolygonInfo:function(e){for(var t=this._triangulationResults[e-this._startIndex],n=0,r=0,i=0;i<t.length;i++)n+=t[i].points.length/3,r+=t[i].indices.length/3;return{vertexCount:n*2+n*4,triangleCount:r*2+n*2}},_updatePolygonGeometry:function(e,t,n,r,i,a,o){var s=e.get(`projectUVOnGround`),c=t.attributes.position,l=t.attributes.normal,u=t.attributes.texcoord0,d=t.attributes.color,f=this._triangulationResults[n-this._startIndex],p=d.value&&o,m=t.indices,h=this.extrudeY?1:2,g=this.extrudeY?2:1,_=[this.rootNode.worldTransform.x.len(),this.rootNode.worldTransform.y.len(),this.rootNode.worldTransform.z.len()],v=pc.mul([],this._geoBoundingBox[0],_),y=pc.mul([],this._geoBoundingBox[1],_),b=Math.max(y[0]-v[0],y[2]-v[2]);function x(e,t,n){for(var r=e.points,a=r.length,s=[],l=[],f=0;f<a;f+=3)s[0]=r[f],s[h]=t,s[g]=r[f+2],l[0]=(r[f]*_[0]-v[0])/b,l[1]=(r[f+2]*_[g]-v[2])/b,c.set(i,s),p&&d.set(i,o),u.set(i++,l)}function S(e,t,n){var r=i;x(e,t,n);for(var o=e.indices.length,s=0;s<o;s++)m[a*3+s]=e.indices[s]+r;a+=e.indices.length/3}for(var C=this.extrudeY?[0,1,0]:[0,0,1],w=pc.negate([],C),T=0;T<f.length;T++){var E=i,D=f[T];S(D,0,0),S(D,r,0);for(var O=D.points.length/3,k=0;k<O;k++)l.set(E+k,w),l.set(E+k+O,C);for(var A=[0,3,1,1,3,2],j=[[],[],[],[]],M=[],N=[],ee=[],te=[],P=0,k=0;k<O;k++){for(var ne=(k+1)%O,re=(D.points[ne*3]-D.points[k*3])*_[0],ie=(D.points[ne*3+2]-D.points[k*3+2])*_[g],ae=Math.sqrt(re*re+ie*ie),F=0;F<4;F++){var oe=F===0||F===3,se=(oe?k:ne)*3;j[F][0]=D.points[se],j[F][h]=F>1?r:0,j[F][g]=D.points[se+2],c.set(i+F,j[F]),s?(te[0]=(D.points[se]*_[0]-v[0])/b,te[1]=(D.points[se+2]*_[g]-v[g])/b):(te[0]=(oe?P:P+ae)/b,te[1]=(j[F][h]*_[h]-v[h])/b),u.set(i+F,te)}pc.sub(M,j[1],j[0]),pc.sub(N,j[3],j[0]),pc.cross(ee,M,N),pc.normalize(ee,ee);for(var F=0;F<4;F++)l.set(i+F,ee),p&&d.set(i+F,o);for(var F=0;F<6;F++)m[a*3+F]=A[F]+i;i+=4,a+=2,P+=ae}}return t.dirty(),{vertexOffset:i,triangleOffset:a}},_getRegionLinesInfo:function(e,t,n){var r=0,i=0;return t.getRegionModel(e).getModel(`itemStyle`).get(`borderWidth`)>0&&t.getRegionPolygonCoords(e).forEach(function(e){var t=e.exterior,a=e.interiors;r+=n.getPolylineVertexCount(t),i+=n.getPolylineTriangleCount(t);for(var o=0;o<a.length;o++)r+=n.getPolylineVertexCount(a[o]),i+=n.getPolylineTriangleCount(a[o])},this),{vertexCount:r,triangleCount:i}},_updateLinesGeometry:function(e,t,n,r,i,a){function o(e){for(var t=new Float64Array(e.length*3),n=0,i=[],o=0;o<e.length;o++)i[0]=e[o][0],i[1]=r+.1,i[2]=e[o][1],a&&pc.transformMat4(i,i,a),t[n++]=i[0],t[n++]=i[1],t[n++]=i[2];return t}var s=[1,1,1,1];t.getRegionPolygonCoords(n).forEach(function(t){var n=t.exterior,r=t.interiors;e.addPolyline(o(n),s,i);for(var a=0;a<r.length;a++)e.addPolyline(o(r[a]),s,i)})},highlight:function(e){var t=this._data;if(t){var n=t.getItemModel(e).getModel([`emphasis`,`itemStyle`]),r=n.get(`color`),i=X.firstNotNull(n.get(`opacity`),lc(t,e),1);r==null&&(r=de(cc(t,e),-.4)),i==null&&(i=lc(t,e));var a=Q.parseColor(r);a[3]*=i,this._setColorOfDataIndex(t,e,a)}},downplay:function(e){var t=this._data;if(t){var n=t.getItemModel(e),r=X.firstNotNull(cc(t,e),n.get([`itemStyle`,`color`]),`#fff`),i=X.firstNotNull(lc(t,e),n.get([`itemStyle`,`opacity`]),1),a=Q.parseColor(r);a[3]*=i,this._setColorOfDataIndex(t,e,a)}},dispose:function(){this._labelsBuilder.dispose()},_setColorOfDataIndex:function(e,t,n){if(!(t<this._startIndex&&t>this._endIndex)){t-=this._startIndex;for(var r=this._vertexRangeOfDataIndex[t*2];r<this._vertexRangeOfDataIndex[t*2+1];r++)this._polygonMesh.geometry.attributes.color.set(r,n);this._polygonMesh.geometry.dirty(),this._api.getZr().refresh()}}};var hc=fe.extend({type:`geo3D`,__ecgl__:!0,init:function(e,t){this._geo3DBuilder=new mc(t),this.groupGL=new Q.Node,this._lightRoot=new Q.Node,this._sceneHelper=new Ma(this._lightRoot),this._sceneHelper.initLight(this._lightRoot),this._control=new wa({zr:t.getZr()}),this._control.init()},render:function(e,t,n){this.groupGL.add(this._geo3DBuilder.rootNode);var r=e.coordinateSystem;if(!(!r||!r.viewGL)){r.viewGL.add(this._lightRoot),e.get(`show`)?r.viewGL.add(this.groupGL):r.viewGL.remove(this.groupGL);var i=this._control;i.setViewGL(r.viewGL);var a=e.getModel(`viewControl`);i.setFromViewControlModel(a,0),this._sceneHelper.setScene(r.viewGL.scene),this._sceneHelper.updateLight(e),r.viewGL.setPostEffect(e.getModel(`postEffect`),n),r.viewGL.setTemporalSuperSampling(e.getModel(`temporalSuperSampling`)),this._geo3DBuilder.update(e,t,n,0,e.getData().count());var o=r.viewGL.isLinearSpace()?`define`:`undefine`;this._geo3DBuilder.rootNode.traverse(function(e){e.material&&e.material[o](`fragment`,`SRGB_DECODE`)}),i.off(`update`),i.on(`update`,function(){n.dispatchAction({type:`geo3DChangeCamera`,alpha:i.getAlpha(),beta:i.getBeta(),distance:i.getDistance(),center:i.getCenter(),from:this.uid,geo3DId:e.id})}),i.update()}},afterRender:function(e,t,n,r){var i=r.renderer;this._sceneHelper.updateAmbientCubemap(i,e,n),this._sceneHelper.updateSkybox(i,e,n)},dispose:function(){this._control.dispose(),this._geo3DBuilder.dispose()}}),gc=Ea.vec3,_c=Ea.mat4,vc=[be,ce];function yc(e,t,n,r,i){this.name=e,this.map=t,this.regionHeight=0,this.regions=[],this._nameCoordMap={},this.loadGeoJson(n,r,i),this.transform=_c.identity(new Float64Array(16)),this.invTransform=_c.identity(new Float64Array(16)),this.extrudeY=!0,this.altitudeAxis}yc.prototype={constructor:yc,type:`geo3D`,dimensions:[`lng`,`lat`,`alt`],containPoint:function(){},loadGeoJson:function(e,t,n){var r=p||p;try{this.regions=e?r(e):[]}catch(e){throw`Invalid geoJson format
`+e}t=t||{},n=n||{};for(var i=this.regions,a={},o=0;o<i.length;o++){var s=i[o].name;s=n[s]||s,i[o].name=s,a[s]=i[o],this.addGeoCoord(s,i[o].getCenter());var c=t[s];c&&i[o].transformTo(c.left,c.top,c.width,c.height)}this._regionsMap=a,this._geoRect=null,vc.forEach(function(e){e(this)},this)},getGeoBoundingRect:function(){if(this._geoRect)return this._geoRect;for(var e,t=this.regions,n=0;n<t.length;n++){var r=t[n].getBoundingRect();e=e||r.clone(),e.union(r)}return this._geoRect=e||new k(0,0,0,0)},addGeoCoord:function(e,t){this._nameCoordMap[e]=t},getRegion:function(e){return this._regionsMap[e]},getRegionByCoord:function(e){for(var t=this.regions,n=0;n<t.length;n++)if(t[n].contain(e))return t[n]},setSize:function(e,t,n){this.size=[e,t,n];var r=this.getGeoBoundingRect(),i=e/r.width,a=-n/r.height,o=-e/2-r.x*i,s=n/2-r.y*a,c=this.extrudeY?[o,0,s]:[o,s,0],l=this.extrudeY?[i,1,a]:[i,a,1],u=this.transform;_c.identity(u),_c.translate(u,u,c),_c.scale(u,u,l),_c.invert(this.invTransform,u)},dataToPoint:function(e,t){t=t||[];var n=this.extrudeY?1:2,r=this.extrudeY?2:1,i=e[2];return isNaN(i)&&(i=0),t[0]=e[0],t[r]=e[1],this.altitudeAxis?t[n]=this.altitudeAxis.dataToCoord(i):t[n]=0,t[n]+=this.regionHeight,gc.transformMat4(t,t,this.transform),t},pointToData:function(e,t){}};function bc(e,t){var n=E(e.getBoxLayoutParams(),{width:t.getWidth(),height:t.getHeight()});n.y=t.getHeight()-n.y-n.height,this.viewGL.setViewport(n.x,n.y,n.width,n.height,t.getDevicePixelRatio());var r=this.getGeoBoundingRect(),i=r.width/r.height*(e.get(`aspectScale`)||.75),a=e.get(`boxWidth`),o=e.get(`boxDepth`),s=e.get(`boxHeight`);s==null&&(s=5),isNaN(a)&&isNaN(o)&&(a=100),isNaN(o)?o=a/i:isNaN(a)&&(a=o/i),this.setSize(a,s,o),this.regionHeight=e.get(`regionHeight`),this.altitudeAxis&&this.altitudeAxis.setExtent(0,Math.max(s-this.regionHeight,0))}function xc(e,t){var n=[1/0,-1/0];if(e.eachSeries(function(e){if(e.coordinateSystem===this&&e.type!==`series.map3D`){var t=e.getData(),r=e.coordDimToDataDim(`alt`),i=r&&r[0];if(i){var a=t.getDataExtent(i,!0);n[0]=Math.min(n[0],a[0]),n[1]=Math.max(n[1],a[1])}}},this),n&&isFinite(n[1]-n[0])){var r=o(n,{type:`value`,min:`dataMin`,max:`dataMax`});this.altitudeAxis=new ie(`altitude`,r),this.resize(this.model,t)}}var Sc=0,Cc={dimensions:yc.prototype.dimensions,create:function(e,t){var n=[];if(!c)throw Error(`geo3D component depends on geo component`);function r(e,r){var i=Cc.createGeo3D(e);e.__viewGL=e.__viewGL||new ns,i.viewGL=e.__viewGL,e.coordinateSystem=i,i.model=e,n.push(i),i.resize=bc,i.resize(e,t),i.update=xc}return e.eachComponent(`geo3D`,function(e,t){r(e,t)}),e.eachSeriesByType(`map3D`,function(e,t){var n=e.get(`coordinateSystem`);n==null&&(n=`geo3D`),n===`geo3D`&&r(e,t)}),e.eachSeries(function(t){if(t.get(`coordinateSystem`)===`geo3D`){if(t.type===`series.map3D`)return;var n=t.getReferringComponents(`geo3D`).models[0];if(n||(n=e.getComponent(`geo3D`)),!n)throw Error(`geo "`+X.firstNotNull(t.get(`geo3DIndex`),t.get(`geo3DId`),0)+`" not found`);t.coordinateSystem=n.coordinateSystem}}),n},createGeo3D:function(e){var t=e.get(`map`),n;return typeof t==`string`?(n=t,t=c(t)):t&&t.features&&(t={geoJson:t}),n==null&&(n=`GEO_ANONYMOUS_`+Sc++),new yc(n+Sc++,n,t&&t.geoJson,t&&t.specialAreas,e.get(`nameMap`))}},wc=`__ECGL_GEO3D_REGISTERED`;function Tc(e){e[wc]||(e[wc]=!0,e.registerComponentModel(bs),e.registerComponentView(hc),e.registerAction({type:`geo3DChangeCamera`,event:`geo3dcamerachanged`,update:`series:updateCamera`},function(e,t){t.eachComponent({mainType:`geo3D`,query:e},function(t){t.setView(e)})}),e.registerCoordinateSystem(`geo3D`,Cc))}h(Tc);function Ec(e,t){e.id=e.id||e.name||t+``}var Dc=D.extend({type:`globe`,layoutMode:`box`,coordinateSystem:null,init:function(){Dc.superApply(this,`init`,arguments),a(this.option.layers,function(e,t){m(e,this.defaultLayerOption),Ec(e,t)},this)},mergeOption:function(e){var t=this.option.layers;this.option.layers=null,Dc.superApply(this,`mergeOption`,arguments);function n(e){return g(e,function(e,t,n){return Ec(t,n),e[t.id]=t,e},{})}if(t&&t.length){var r=n(e.layers),i=n(t);for(var o in r)i[o]?m(i[o],r[o],!0):t.push(e.layers[o]);this.option.layers=t}a(this.option.layers,function(e){m(e,this.defaultLayerOption)},this)},optionUpdated:function(){this.updateDisplacementHash()},defaultLayerOption:{show:!0,type:`overlay`},defaultOption:{show:!0,zlevel:-10,left:0,top:0,width:`100%`,height:`100%`,environment:`auto`,baseColor:`#fff`,baseTexture:``,heightTexture:``,displacementTexture:``,displacementScale:0,displacementQuality:`medium`,globeRadius:100,globeOuterRadius:150,shading:`lambert`,light:{main:{time:``}},atmosphere:{show:!1,offset:5,color:`#ffffff`,glowPower:6,innerGlowPower:2},viewControl:{autoRotate:!0,panSensitivity:0,targetCoord:null},layers:[]},setDisplacementData:function(e,t,n){this.displacementData=e,this.displacementWidth=t,this.displacementHeight=n},getDisplacementTexture:function(){return this.get(`displacementTexture`)||this.get(`heightTexture`)},getDisplacemenScale:function(){var e=this.getDisplacementTexture(),t=this.get(`displacementScale`);return(!e||e===`none`)&&(t=0),t},hasDisplacement:function(){return this.getDisplacemenScale()>0},_displacementChanged:!0,_displacementScale:0,updateDisplacementHash:function(){var e=this.getDisplacementTexture(),t=this.getDisplacemenScale();this._displacementChanged=this._displacementTexture!==e||this._displacementScale!==t,this._displacementTexture=e,this._displacementScale=t},isDisplacementChanged:function(){return this._displacementChanged}});m(Dc.prototype,_a),m(Dc.prototype,va),m(Dc.prototype,ya),m(Dc.prototype,vs);var Oc=Math.PI,kc=Math.sin,Ac=Math.cos,jc=Math.tan,Mc=Math.asin,Nc=Math.atan2,Pc=Oc/180,Fc=1e3*60*60*24,Ic=2440588,Lc=2451545;function Rc(e){return e.valueOf()/Fc-.5+Ic}function zc(e){return Rc(e)-Lc}var Bc=Pc*23.4397;function Vc(e,t){return Nc(kc(e)*Ac(Bc)-jc(t)*kc(Bc),Ac(e))}function Hc(e,t){return Mc(kc(t)*Ac(Bc)+Ac(t)*kc(Bc)*kc(e))}function Uc(e,t,n){return Nc(kc(e),Ac(e)*kc(t)-jc(n)*Ac(t))}function Wc(e,t,n){return Mc(kc(t)*kc(n)+Ac(t)*Ac(n)*Ac(e))}function Gc(e,t){return Pc*(280.16+360.9856235*e)-t}function Kc(e){return Pc*(357.5291+.98560028*e)}function qc(e){var t=Pc*(1.9148*kc(e)+.02*kc(2*e)+3e-4*kc(3*e)),n=Pc*102.9372;return e+t+n+Oc}function Jc(e){var t=qc(Kc(e));return{dec:Hc(t,0),ra:Vc(t,0)}}var Yc={};Yc.getPosition=function(e,t,n){var r=Pc*-n,i=Pc*t,a=zc(e),o=Jc(a),s=Gc(a,r)-o.ra;return{azimuth:Uc(s,i,o.dec),altitude:Wc(s,i,o.dec)}},Q.Shader.import(Gi),Q.Shader.import(`@export ecgl.atmosphere.vertex
attribute vec3 position: POSITION;
attribute vec3 normal : NORMAL;
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform mat4 normalMatrix : WORLDINVERSETRANSPOSE;

varying vec3 v_Normal;

void main() {
 v_Normal = normalize((normalMatrix * vec4(normal, 0.0)).xyz);
 gl_Position = worldViewProjection * vec4(position, 1.0);
}
@end


@export ecgl.atmosphere.fragment
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform float glowPower;
uniform vec3 glowColor;

varying vec3 v_Normal;

void main() {
 float intensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor = vec4(glowColor, intensity * intensity);
}
@end`);var Xc=fe.extend({type:`globe`,__ecgl__:!0,_displacementScale:0,init:function(e,t){this.groupGL=new Q.Node,this._sphereGeometry=new Q.SphereGeometry({widthSegments:200,heightSegments:100,dynamic:!0}),this._overlayGeometry=new Q.SphereGeometry({widthSegments:80,heightSegments:40}),this._planeGeometry=new Q.PlaneGeometry,this._earthMesh=new Q.Mesh({renderNormal:!0}),this._atmosphereMesh=new Q.Mesh,this._atmosphereGeometry=new Q.SphereGeometry({widthSegments:80,heightSegments:40}),this._atmosphereMaterial=new Q.Material({shader:new Q.Shader(Q.Shader.source(`ecgl.atmosphere.vertex`),Q.Shader.source(`ecgl.atmosphere.fragment`)),transparent:!0}),this._atmosphereMesh.geometry=this._atmosphereGeometry,this._atmosphereMesh.material=this._atmosphereMaterial,this._atmosphereMesh.frontFace=Q.Mesh.CW,this._lightRoot=new Q.Node,this._sceneHelper=new Ma,this._sceneHelper.initLight(this._lightRoot),this.groupGL.add(this._atmosphereMesh),this.groupGL.add(this._earthMesh),this._control=new wa({zr:t.getZr()}),this._control.init(),this._layerMeshes={}},render:function(e,t,n){var r=e.coordinateSystem,i=e.get(`shading`);r.viewGL.add(this._lightRoot),e.get(`show`)?r.viewGL.add(this.groupGL):r.viewGL.remove(this.groupGL),this._sceneHelper.setScene(r.viewGL.scene),r.viewGL.setPostEffect(e.getModel(`postEffect`),n),r.viewGL.setTemporalSuperSampling(e.getModel(`temporalSuperSampling`));var a=this._earthMesh;a.geometry=this._sphereGeometry;var o=`ecgl.`+i;(!a.material||a.material.shader.name!==o)&&(a.material=Q.createMaterial(o)),Q.setMaterialFromModel(i,a.material,e,n),[`roughnessMap`,`metalnessMap`,`detailMap`,`normalMap`].forEach(function(e){var t=a.material.get(e);t&&(t.flipY=!1)}),a.material.set(`color`,Q.parseColor(e.get(`baseColor`)));var s=r.radius*.99;if(a.scale.set(s,s,s),e.get(`atmosphere.show`)){a.material.define(`both`,`ATMOSPHERE_ENABLED`),this._atmosphereMesh.invisible=!1,this._atmosphereMaterial.setUniforms({glowPower:e.get(`atmosphere.glowPower`)||6,glowColor:e.get(`atmosphere.color`)||`#ffffff`}),a.material.setUniforms({glowPower:e.get(`atmosphere.innerGlowPower`)||2,glowColor:e.get(`atmosphere.color`)||`#ffffff`});var c=e.get(`atmosphere.offset`)||5;this._atmosphereMesh.scale.set(s+c,s+c,s+c)}else a.material.undefine(`both`,`ATMOSPHERE_ENABLED`),this._atmosphereMesh.invisible=!0;var l=a.material.setTextureImage(`diffuseMap`,e.get(`baseTexture`),n,{flipY:!1,anisotropic:8});l&&l.surface&&l.surface.attachToMesh(a);var u=a.material.setTextureImage(`bumpMap`,e.get(`heightTexture`),n,{flipY:!1,anisotropic:8});u&&u.surface&&u.surface.attachToMesh(a),a.material[e.get(`postEffect.enable`)?`define`:`undefine`](`fragment`,`SRGB_DECODE`),this._updateLight(e,n),this._displaceVertices(e,n),this._updateViewControl(e,n),this._updateLayers(e,n)},afterRender:function(e,t,n,r){var i=r.renderer;this._sceneHelper.updateAmbientCubemap(i,e,n),this._sceneHelper.updateSkybox(i,e,n)},_updateLayers:function(e,t){var n=e.coordinateSystem,r=e.get(`layers`),i=n.radius,o=[],s=[],c=[],l=[];a(r,function(e){var r=new _e(e),a=r.get(`type`),u=Q.loadTexture(r.get(`texture`),t,{flipY:!1,anisotropic:8});if(u.surface&&u.surface.attachToMesh(this._earthMesh),a===`blend`){var d=r.get(`blendTo`),f=X.firstNotNull(r.get(`intensity`),1);d===`emission`?(c.push(u),l.push(f)):(o.push(u),s.push(f))}else{var p=r.get(`id`),m=this._layerMeshes[p];m||(m=this._layerMeshes[p]=new Q.Mesh({geometry:this._overlayGeometry,castShadow:!1,ignorePicking:!0})),r.get(`shading`)===`lambert`?(m.material=m.__lambertMaterial||new Q.Material({autoUpdateTextureStatus:!1,shader:Q.createShader(`ecgl.lambert`),transparent:!0,depthMask:!1}),m.__lambertMaterial=m.material):(m.material=m.__colorMaterial||new Q.Material({autoUpdateTextureStatus:!1,shader:Q.createShader(`ecgl.color`),transparent:!0,depthMask:!1}),m.__colorMaterial=m.material),m.material.enableTexture(`diffuseMap`);var h=r.get(`distance`),g=i+(h==null?n.radius/100:h);m.scale.set(g,g,g),i=g;var _=this._blankTexture||(this._blankTexture=Q.createBlankTexture(`rgba(255, 255, 255, 0)`));m.material.set(`diffuseMap`,_),Q.loadTexture(r.get(`texture`),t,{flipY:!1,anisotropic:8},function(e){e.surface&&e.surface.attachToMesh(m),m.material.set(`diffuseMap`,e),t.getZr().refresh()}),r.get(`show`)?this.groupGL.add(m):this.groupGL.remove(m)}},this);var u=this._earthMesh.material;u.define(`fragment`,`LAYER_DIFFUSEMAP_COUNT`,o.length),u.define(`fragment`,`LAYER_EMISSIVEMAP_COUNT`,c.length),u.set(`layerDiffuseMap`,o),u.set(`layerDiffuseIntensity`,s),u.set(`layerEmissiveMap`,c),u.set(`layerEmissionIntensity`,l);var d=e.getModel(`debug.wireframe`);if(d.get(`show`)){u.define(`both`,`WIREFRAME_TRIANGLE`);var f=Q.parseColor(d.get(`lineStyle.color`)||`rgba(0,0,0,0.5)`),p=X.firstNotNull(d.get(`lineStyle.width`),1);u.set(`wireframeLineWidth`,p),u.set(`wireframeLineColor`,f)}else u.undefine(`both`,`WIREFRAME_TRIANGLE`)},_updateViewControl:function(e,t){var n=e.coordinateSystem,r=e.getModel(`viewControl`);n.viewGL.camera;var i=this;function a(){return{type:`globeChangeCamera`,alpha:o.getAlpha(),beta:o.getBeta(),distance:o.getDistance()-n.radius,center:o.getCenter(),from:i.uid,globeId:e.id}}var o=this._control;o.setViewGL(n.viewGL);var s=r.get(`targetCoord`),c,l;s!=null&&(l=s[0]+90,c=s[1]),o.setFromViewControlModel(r,{baseDistance:n.radius,alpha:c,beta:l}),o.off(`update`),o.on(`update`,function(){t.dispatchAction(a())})},_displaceVertices:function(e,t){var n=e.get(`displacementQuality`),r=e.get(`debug.wireframe.show`),i=e.coordinateSystem;if(!(!e.isDisplacementChanged()&&n===this._displacementQuality&&r===this._showDebugWireframe)){this._displacementQuality=n,this._showDebugWireframe=r;var a=this._sphereGeometry,o={low:100,medium:200,high:400,ultra:800}[n]||200,s=o/2;(a.widthSegments!==o||r)&&(a.widthSegments=o,a.heightSegments=s,a.build()),this._doDisplaceVertices(a,i),r&&a.generateBarycentric()}},_doDisplaceVertices:function(e,t){var n=e.attributes.position.value,r=e.attributes.texcoord0.value,i=e.__originalPosition;(!i||i.length!==n.length)&&(i=new Float32Array(n.length),i.set(n),e.__originalPosition=i);for(var a=t.displacementWidth,o=t.displacementHeight,s=t.displacementData,c=0;c<e.vertexCount;c++){var l=c*3,u=c*2,d=i[l+1],f=i[l+2],p=i[l+3],m=r[u++],h=r[u++],g=Math.round(m*(a-1)),_=Math.round(h*(o-1))*a+g,v=s?s[_]:0;n[l+1]=d+d*v,n[l+2]=f+f*v,n[l+3]=p+p*v}e.generateVertexNormals(),e.dirty(),e.updateBoundingBox()},_updateLight:function(e,t){var n=this._earthMesh;this._sceneHelper.updateLight(e);var r=this._sceneHelper.mainLight,i=e.get(`light.main.time`)||new Date,a=Yc.getPosition(oe(i),0,0),o=Math.cos(a.altitude);r.position.y=-o*Math.cos(a.azimuth),r.position.x=Math.sin(a.altitude),r.position.z=o*Math.sin(a.azimuth),r.lookAt(n.getWorldPosition())},dispose:function(e,t){this.groupGL.removeAll(),this._control.dispose()}}),Zc=Ea.vec3;function Qc(e){this.radius=e,this.viewGL=null,this.altitudeAxis,this.displacementData=null,this.displacementWidth,this.displacementHeight}Qc.prototype={constructor:Qc,dimensions:[`lng`,`lat`,`alt`],type:`globe`,containPoint:function(){},setDisplacementData:function(e,t,n){this.displacementData=e,this.displacementWidth=t,this.displacementHeight=n},_getDisplacementScale:function(e,t){var n=(e+180)/360*(this.displacementWidth-1),r=(90-t)/180*(this.displacementHeight-1),i=Math.round(n)+Math.round(r)*this.displacementWidth;return this.displacementData[i]},dataToPoint:function(e,t){var n=e[0],r=e[1],i=e[2]||0,a=this.radius;this.displacementData&&(a*=1+this._getDisplacementScale(n,r)),this.altitudeAxis&&(a+=this.altitudeAxis.dataToCoord(i)),n=n*Math.PI/180,r=r*Math.PI/180;var o=Math.cos(r)*a;return t=t||[],t[0]=-o*Math.cos(n+Math.PI),t[1]=Math.sin(r)*a,t[2]=o*Math.sin(n+Math.PI),t},pointToData:function(e,t){var n=e[0],r=e[1],i=e[2],a=Zc.len(e);n/=a,r/=a,i/=a;var o=Math.asin(r),s=Math.atan2(i,-n);s<0&&(s=Math.PI*2+s);var c=o*180/Math.PI,l=s*180/Math.PI-180;return t=t||[],t[0]=l,t[1]=c,t[2]=a-this.radius,this.altitudeAxis&&(t[2]=this.altitudeAxis.coordToData(t[2])),t}};function $c(e,t){var n=document.createElement(`canvas`),r=n.getContext(`2d`),i=e.width,a=e.height;n.width=i,n.height=a,r.drawImage(e,0,0,i,a);for(var o=r.getImageData(0,0,i,a).data,s=new Float32Array(o.length/4),c=0;c<o.length/4;c++)s[c]=o[c*4]/255*t;return{data:s,width:i,height:a}}function el(e,t){var n=E(e.getBoxLayoutParams(),{width:t.getWidth(),height:t.getHeight()});n.y=t.getHeight()-n.y-n.height,this.viewGL.setViewport(n.x,n.y,n.width,n.height,t.getDevicePixelRatio()),this.radius=e.get(`globeRadius`);var r=e.get(`globeOuterRadius`);this.altitudeAxis&&this.altitudeAxis.setExtent(0,r-this.radius)}function tl(e,t){var n=[1/0,-1/0];if(e.eachSeries(function(e){if(e.coordinateSystem===this){var t=e.getData(),r=e.coordDimToDataDim(`alt`),i=r&&r[0];if(i){var a=t.getDataExtent(i,!0);n[0]=Math.min(n[0],a[0]),n[1]=Math.max(n[1],a[1])}}},this),n&&isFinite(n[1]-n[0])){var r=o(n,{type:`value`,min:`dataMin`,max:`dataMax`});this.altitudeAxis=new ie(`altitude`,r),this.resize(this.model,t)}}var nl={dimensions:Qc.prototype.dimensions,create:function(e,t){var n=[];return e.eachComponent(`globe`,function(e){e.__viewGL=e.__viewGL||new ns;var r=new Qc;r.viewGL=e.__viewGL,e.coordinateSystem=r,r.model=e,n.push(r),r.resize=el,r.resize(e,t),r.update=tl}),e.eachSeries(function(t){if(t.get(`coordinateSystem`)===`globe`){var n=t.getReferringComponents(`globe`).models[0];if(n||(n=e.getComponent(`globe`)),!n)throw Error(`globe "`+X.firstNotNull(t.get(`globe3DIndex`),t.get(`globe3DId`),0)+`" not found`);t.coordinateSystem=n.coordinateSystem}}),e.eachComponent(`globe`,function(e,n){var r=e.coordinateSystem,i=e.getDisplacementTexture(),a=e.getDisplacemenScale();if(e.isDisplacementChanged()){if(e.hasDisplacement()){var o=!0;Q.loadTexture(i,t,function(n){var r=n.image,i=$c(r,a);e.setDisplacementData(i.data,i.width,i.height),o||t.dispatchAction({type:`globeUpdateDisplacment`})}),o=!1}else r.setDisplacementData(null,0,0);r.setDisplacementData(e.displacementData,e.displacementWidth,e.displacementHeight)}}),n}};function rl(e){e.registerComponentModel(Dc),e.registerComponentView(Xc),e.registerCoordinateSystem(`globe`,nl),e.registerAction({type:`globeChangeCamera`,event:`globecamerachanged`,update:`series:updateCamera`},function(e,t){t.eachComponent({mainType:`globe`,query:e},function(t){t.setView(e)})}),e.registerAction({type:`globeUpdateDisplacment`,event:`globedisplacementupdated`,update:`update`},function(e,t){})}h(rl);var il=[`zoom`,`center`,`pitch`,`bearing`],al=D.extend({type:`mapbox3D`,layoutMode:`box`,coordinateSystem:null,defaultOption:{zlevel:-10,style:`mapbox://styles/mapbox/light-v9`,center:[0,0],zoom:0,pitch:0,bearing:0,light:{main:{alpha:20,beta:30}},altitudeScale:1,boxHeight:`auto`},getMapboxCameraOption:function(){var e=this;return il.reduce(function(t,n){return t[n]=e.get(n),t},{})},setMapboxCameraOption:function(e){e!=null&&il.forEach(function(t){e[t]!=null&&(this.option[t]=e[t])},this)},getMapbox:function(){return this._mapbox},setMapbox:function(e){this._mapbox=e}});m(al.prototype,va),m(al.prototype,ya);function ol(e,t){if(this.id=e,this.zr=t,this.dom=document.createElement(`div`),this.dom.style.cssText=`position:absolute;left:0;right:0;top:0;bottom:0;`,!mapboxgl)throw Error(`Mapbox GL library must be included. See https://www.mapbox.com/mapbox-gl-js/api/`);this._mapbox=new mapboxgl.Map({container:this.dom}),this._initEvents()}ol.prototype.setUnpainted=function(){},ol.prototype.resize=function(){this._mapbox.resize()},ol.prototype.getMapbox=function(){return this._mapbox},ol.prototype.clear=function(){},ol.prototype.refresh=function(){this._mapbox.resize()};var sl=[`mousedown`,`mouseup`,`click`,`dblclick`,`mousemove`,`mousewheel`,`wheel`,`touchstart`,`touchend`,`touchmove`,`touchcancel`];ol.prototype._initEvents=function(){var e=this._mapbox.getCanvasContainer();this._handlers=this._handlers||{contextmenu:function(e){return e.preventDefault(),!1}},sl.forEach(function(t){this._handlers[t]=function(t){var n={};for(var r in t)n[r]=t[r];n.bubbles=!1;var i=new t.constructor(t.type,n);e.dispatchEvent(i)},this.zr.dom.addEventListener(t,this._handlers[t])},this),this.zr.dom.addEventListener(`contextmenu`,this._handlers.contextmenu)},ol.prototype.dispose=function(){sl.forEach(function(e){this.zr.dom.removeEventListener(e,this._handlers[e])},this)};var cl=`
@export ecgl.displayShadow.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header

@import ecgl.common.attributes

varying vec3 v_WorldPosition;

varying vec3 v_Normal;

void main()
{
 @import ecgl.common.uv.main
 v_Normal = normalize((worldInverseTranspose * vec4(normal, 0.0)).xyz);

 v_WorldPosition = (world * vec4(position, 1.0)).xyz;
 gl_Position = worldViewProjection * vec4(position, 1.0);
}

@end


@export ecgl.displayShadow.fragment

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform float roughness: 0.2;

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

@import ecgl.common.ssaoMap.header

@import clay.plugin.compute_shadow_map

void main()
{
 float shadow = 1.0;

 @import ecgl.common.ssaoMap.main

#if defined(DIRECTIONAL_LIGHT_COUNT) && defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
 for (int i = 0; i < DIRECTIONAL_LIGHT_COUNT; i++) {
 shadow = min(shadow, shadowContribsDir[i] * 0.5 + 0.5);
 }
#endif

 shadow *= 0.5 + ao * 0.5;
 shadow = clamp(shadow, 0.0, 1.0);

 gl_FragColor = vec4(vec3(0.0), 1.0 - shadow);
}

@end`;Q.Shader.import(cl);var ll=fe.extend({type:`mapbox3D`,__ecgl__:!0,init:function(e,t){var n=t.getZr();this._zrLayer=new ol(`mapbox3D`,n),n.painter.insertLayer(-1e3,this._zrLayer),this._lightRoot=new Q.Node,this._sceneHelper=new Ma(this._lightRoot),this._sceneHelper.initLight(this._lightRoot);var r=this._zrLayer.getMapbox(),i=this._dispatchInteractAction.bind(this,t,r);[`zoom`,`rotate`,`drag`,`pitch`,`rotate`,`move`].forEach(function(e){r.on(e,i)}),this._groundMesh=new Q.Mesh({geometry:new Q.PlaneGeometry,material:new Q.Material({shader:new Q.Shader({vertex:Q.Shader.source(`ecgl.displayShadow.vertex`),fragment:Q.Shader.source(`ecgl.displayShadow.fragment`)}),depthMask:!1}),renderOrder:-100,culling:!1,castShadow:!1,$ignorePicking:!0,renderNormal:!0})},render:function(e,t,n){var r=this._zrLayer.getMapbox(),i=e.get(`style`),a=JSON.stringify(i);a!==this._oldStyleStr&&i&&r.setStyle(i),this._oldStyleStr=a,r.setCenter(e.get(`center`)),r.setZoom(e.get(`zoom`)),r.setPitch(e.get(`pitch`)),r.setBearing(e.get(`bearing`)),e.setMapbox(r);var o=e.coordinateSystem;o.viewGL.scene.add(this._lightRoot),o.viewGL.add(this._groundMesh),this._updateGroundMesh(),this._sceneHelper.setScene(o.viewGL.scene),this._sceneHelper.updateLight(e),o.viewGL.setPostEffect(e.getModel(`postEffect`),n),o.viewGL.setTemporalSuperSampling(e.getModel(`temporalSuperSampling`)),this._mapbox3DModel=e},afterRender:function(e,t,n,r){var i=r.renderer;this._sceneHelper.updateAmbientCubemap(i,e,n),this._sceneHelper.updateSkybox(i,e,n),e.coordinateSystem.viewGL.scene.traverse(function(e){e.material&&(e.material.define(`fragment`,`NORMAL_UP_AXIS`,2),e.material.define(`fragment`,`NORMAL_FRONT_AXIS`,1))})},updateCamera:function(e,t,n,r){e.coordinateSystem.setCameraOption(r),this._updateGroundMesh(),n.getZr().refresh()},_dispatchInteractAction:function(e,t,n){e.dispatchAction({type:`mapbox3DChangeCamera`,pitch:t.getPitch(),zoom:t.getZoom(),center:t.getCenter().toArray(),bearing:t.getBearing(),mapbox3DId:this._mapbox3DModel&&this._mapbox3DModel.id})},_updateGroundMesh:function(){if(this._mapbox3DModel){var e=this._mapbox3DModel.coordinateSystem,t=e.dataToPoint(e.center);this._groundMesh.position.set(t[0],t[1],-.001);var n=new Q.Plane(new Q.Vector3(0,0,1),0),r=e.viewGL.camera.castRay(new Q.Vector2(-1,-1)),i=e.viewGL.camera.castRay(new Q.Vector2(1,1)),a=r.intersectPlane(n),o=i.intersectPlane(n),s=a.dist(o)/e.viewGL.rootNode.scale.x;this._groundMesh.scale.set(s,s,1)}},dispose:function(e,t){this._zrLayer&&this._zrLayer.dispose(),t.getZr().painter.delLayer(-1e3)}}),ul=Ea.mat4,dl=512,fl=.6435011087932844,pl=Math.PI,ml=1/10;function hl(){this.width=0,this.height=0,this.altitudeScale=1,this.boxHeight=`auto`,this.altitudeExtent,this.bearing=0,this.pitch=0,this.center=[0,0],this._origin,this.zoom=0,this._initialZoom,this.maxPitch=60,this.zoomOffset=0}hl.prototype={constructor:hl,dimensions:[`lng`,`lat`,`alt`],containPoint:function(){},setCameraOption:function(e){this.bearing=e.bearing,this.pitch=e.pitch,this.center=e.center,this.zoom=e.zoom,this._origin||(this._origin=this.projectOnTileWithScale(this.center,dl)),this._initialZoom==null&&(this._initialZoom=this.zoom),this.updateTransform()},updateTransform:function(){if(this.height){var e=.5/Math.tan(fl/2)*this.height*ml,t=Math.max(Math.min(this.pitch,this.maxPitch),0)/180*Math.PI,n=fl/2,r=Math.PI/2+t,i=Math.sin(n)*e/Math.sin(Math.PI-r-n),a=(Math.cos(Math.PI/2-t)*i+e)*1.1;this.pitch>50&&(a=1e3);var o=[];ul.perspective(o,fl,this.width/this.height,1,a),this.viewGL.camera.projectionMatrix.setArray(o),this.viewGL.camera.decomposeProjectionMatrix();var o=ul.identity([]),s=this.dataToPoint(this.center);ul.scale(o,o,[1,-1,1]),ul.translate(o,o,[0,0,-e]),ul.rotateX(o,o,t),ul.rotateZ(o,o,-this.bearing/180*Math.PI),ul.translate(o,o,[-s[0]*this.getScale()*ml,-s[1]*this.getScale()*ml,0]),this.viewGL.camera.viewMatrix.array=o;var c=[];ul.invert(c,o),this.viewGL.camera.worldTransform.array=c,this.viewGL.camera.decomposeWorldTransform();var l=dl*this.getScale(),u;if(this.altitudeExtent&&!isNaN(this.boxHeight)){var d=this.altitudeExtent[1]-this.altitudeExtent[0];u=this.boxHeight/d*this.getScale()/2**(this._initialZoom-this.zoomOffset)}else u=l/(2*Math.PI*6378e3*Math.abs(Math.cos(this.center[1]*(Math.PI/180))))*this.altitudeScale*ml;this.viewGL.rootNode.scale.set(this.getScale()*ml,this.getScale()*ml,u)}},getScale:function(){return 2**(this.zoom-this.zoomOffset)},projectOnTile:function(e,t){return this.projectOnTileWithScale(e,this.getScale()*dl,t)},projectOnTileWithScale:function(e,t,n){var r=e[0],i=e[1],a=r*pl/180,o=i*pl/180,s=t*(a+pl)/(2*pl),c=t*(pl-Math.log(Math.tan(pl/4+o*.5)))/(2*pl);return n=n||[],n[0]=s,n[1]=c,n},unprojectFromTile:function(e,t){return this.unprojectOnTileWithScale(e,this.getScale()*dl,t)},unprojectOnTileWithScale:function(e,t,n){var r=e[0],i=e[1],a=r/t*(2*pl)-pl,o=2*(Math.atan(Math.exp(pl-i/t*(2*pl)))-pl/4);return n=n||[],n[0]=a*180/pl,n[1]=o*180/pl,n},dataToPoint:function(e,t){return t=this.projectOnTileWithScale(e,dl,t),t[0]-=this._origin[0],t[1]-=this._origin[1],t[2]=isNaN(e[2])?0:e[2],isNaN(e[2])||(t[2]=e[2],this.altitudeExtent&&(t[2]-=this.altitudeExtent[0])),t}};function gl(){hl.apply(this,arguments)}gl.prototype=new hl,gl.prototype.constructor=gl,gl.prototype.type=`mapbox3D`;function _l(e,t,n){function r(e,t){var n=t.getWidth(),r=t.getHeight(),i=t.getDevicePixelRatio();this.viewGL.setViewport(0,0,n,r,i),this.width=n,this.height=r,this.altitudeScale=e.get(`altitudeScale`),this.boxHeight=e.get(`boxHeight`)}function i(e,t){if(this.model.get(`boxHeight`)!==`auto`){var n=[1/0,-1/0];e.eachSeries(function(e){if(e.coordinateSystem===this){var t=e.getData(),r=e.coordDimToDataDim(`alt`)[0];if(r){var i=t.getDataExtent(r,!0);n[0]=Math.min(n[0],i[0]),n[1]=Math.max(n[1],i[1])}}},this),n&&isFinite(n[1]-n[0])&&(this.altitudeExtent=n)}}return{dimensions:t.prototype.dimensions,create:function(a,o){var s=[];return a.eachComponent(e,function(e){var n=e.__viewGL;n||(n=e.__viewGL=new ns,n.setRootNode(new Q.Node));var a=new t;a.viewGL=e.__viewGL,a.resize=r,a.resize(e,o),s.push(a),e.coordinateSystem=a,a.model=e,a.update=i}),a.eachSeries(function(t){if(t.get(`coordinateSystem`)===e){var n=t.getReferringComponents(e).models[0];if(n||(n=a.getComponent(e)),!n)throw Error(e+` "`+X.firstNotNull(t.get(e+`Index`),t.get(e+`Id`),0)+`" not found`);t.coordinateSystem=n.coordinateSystem}}),n&&n(s,a,o),s}}}var vl=_l(`mapbox3D`,gl,function(e){e.forEach(function(e){e.setCameraOption(e.model.getMapboxCameraOption())})});function yl(e){e.registerComponentModel(al),e.registerComponentView(ll),e.registerCoordinateSystem(`mapbox3D`,vl),e.registerAction({type:`mapbox3DChangeCamera`,event:`mapbox3dcamerachanged`,update:`mapbox3D:updateCamera`},function(e,t){t.eachComponent({mainType:`mapbox3D`,query:e},function(t){t.setMapboxCameraOption(e)})})}h(yl);var bl=[`zoom`,`center`,`pitch`,`bearing`],xl=D.extend({type:`maptalks3D`,layoutMode:`box`,coordinateSystem:null,defaultOption:{zlevel:-10,urlTemplate:`http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png`,attribution:`&copy; <a href="http://osm.org">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/">CARTO</a>`,center:[0,0],zoom:0,pitch:0,bearing:0,light:{main:{alpha:20,beta:30}},altitudeScale:1,boxHeight:`auto`},getMaptalksCameraOption:function(){var e=this;return bl.reduce(function(t,n){return t[n]=e.get(n),t},{})},setMaptalksCameraOption:function(e){e!=null&&bl.forEach(function(t){e[t]!=null&&(this.option[t]=e[t])},this)},getMaptalks:function(){return this._maptalks},setMaptalks:function(e){this._maptalks=e}});m(xl.prototype,va),m(xl.prototype,ya);function Sl(e,t,n,r){if(this.id=e,this.zr=t,this.dom=document.createElement(`div`),this.dom.style.cssText=`position:absolute;left:0;right:0;top:0;bottom:0;`,!maptalks)throw Error(`Maptalks library must be included. See https://maptalks.org`);this._maptalks=new maptalks.Map(this.dom,{center:n,zoom:r,doubleClickZoom:!1,fog:!1}),this._initEvents()}Sl.prototype.setUnpainted=function(){},Sl.prototype.resize=function(){this._maptalks.checkSize()},Sl.prototype.getMaptalks=function(){return this._maptalks},Sl.prototype.clear=function(){},Sl.prototype.refresh=function(){this._maptalks.checkSize()};var Cl=[`mousedown`,`mouseup`,`click`,`dblclick`,`mousemove`,`mousewheel`,`DOMMouseScroll`,`touchstart`,`touchend`,`touchmove`,`touchcancel`];Sl.prototype._initEvents=function(){var e=this.dom;this._handlers=this._handlers||{contextmenu:function(e){return e.preventDefault(),!1}},Cl.forEach(function(t){this._handlers[t]=function(n){var r={};for(var i in n)r[i]=n[i];r.bubbles=!1;var a=new n.constructor(n.type,r);t===`mousewheel`||t===`DOMMouseScroll`?e.dispatchEvent(a):e.firstElementChild.dispatchEvent(a)},this.zr.dom.addEventListener(t,this._handlers[t])},this),this.zr.dom.addEventListener(`contextmenu`,this._handlers.contextmenu)},Sl.prototype.dispose=function(){Cl.forEach(function(e){this.zr.dom.removeEventListener(e,this._handlers[e])},this),this._maptalks.remove()},Q.Shader.import(cl);var wl=fe.extend({type:`maptalks3D`,__ecgl__:!0,init:function(e,t){this._groundMesh=new Q.Mesh({geometry:new Q.PlaneGeometry,material:new Q.Material({shader:new Q.Shader({vertex:Q.Shader.source(`ecgl.displayShadow.vertex`),fragment:Q.Shader.source(`ecgl.displayShadow.fragment`)}),depthMask:!1}),renderOrder:-100,culling:!1,castShadow:!1,$ignorePicking:!0,renderNormal:!0})},_initMaptalksLayer:function(e,t){var n=t.getZr();this._zrLayer=new Sl(`maptalks3D`,n,e.get(`center`),e.get(`zoom`)),n.painter.insertLayer(-1e3,this._zrLayer),this._lightRoot=new Q.Node,this._sceneHelper=new Ma(this._lightRoot),this._sceneHelper.initLight(this._lightRoot);var r=this._zrLayer.getMaptalks(),i=this._dispatchInteractAction.bind(this,t,r);[`zoomend`,`zooming`,`zoomstart`,`dragrotating`,`pitch`,`pitchend`,`movestart`,`moving`,`moveend`,`resize`,`touchstart`,`touchmove`,`touchend`,`animating`].forEach(function(e){r.on(e,i)})},render:function(e,t,n){this._zrLayer||this._initMaptalksLayer(e,n);var r=this._zrLayer.getMaptalks(),i=e.get(`urlTemplate`),a=r.getBaseLayer();i!==this._oldUrlTemplate&&(a?a.setOptions({urlTemplate:i,attribution:e.get(`attribution`)}):(a=new maptalks.TileLayer(`maptalks-echarts-gl-baselayer`,{urlTemplate:i,subdomains:[`a`,`b`,`c`],attribution:e.get(`attribution`)}),r.setBaseLayer(a))),this._oldUrlTemplate=i,r.setCenter(e.get(`center`)),r.setZoom(e.get(`zoom`),{animation:!1}),r.setPitch(e.get(`pitch`)),r.setBearing(e.get(`bearing`)),e.setMaptalks(r);var o=e.coordinateSystem;o.viewGL.scene.add(this._lightRoot),o.viewGL.add(this._groundMesh),this._updateGroundMesh(),this._sceneHelper.setScene(o.viewGL.scene),this._sceneHelper.updateLight(e),o.viewGL.setPostEffect(e.getModel(`postEffect`),n),o.viewGL.setTemporalSuperSampling(e.getModel(`temporalSuperSampling`)),this._maptalks3DModel=e},afterRender:function(e,t,n,r){var i=r.renderer;this._sceneHelper.updateAmbientCubemap(i,e,n),this._sceneHelper.updateSkybox(i,e,n),e.coordinateSystem.viewGL.scene.traverse(function(e){e.material&&(e.material.define(`fragment`,`NORMAL_UP_AXIS`,2),e.material.define(`fragment`,`NORMAL_FRONT_AXIS`,1))})},updateCamera:function(e,t,n,r){e.coordinateSystem.setCameraOption(r),this._updateGroundMesh(),n.getZr().refresh()},_dispatchInteractAction:function(e,t,n){e.dispatchAction({type:`maptalks3DChangeCamera`,pitch:t.getPitch(),zoom:El(t.getResolution())+1,center:t.getCenter().toArray(),bearing:t.getBearing(),maptalks3DId:this._maptalks3DModel&&this._maptalks3DModel.id})},_updateGroundMesh:function(){if(this._maptalks3DModel){var e=this._maptalks3DModel.coordinateSystem,t=e.dataToPoint(e.center);this._groundMesh.position.set(t[0],t[1],-.001);var n=new Q.Plane(new Q.Vector3(0,0,1),0),r=e.viewGL.camera.castRay(new Q.Vector2(-1,-1)),i=e.viewGL.camera.castRay(new Q.Vector2(1,1)),a=r.intersectPlane(n),o=i.intersectPlane(n),s=a.dist(o)/e.viewGL.rootNode.scale.x;this._groundMesh.scale.set(s,s,1)}},dispose:function(e,t){this._zrLayer&&this._zrLayer.dispose(),t.getZr().painter.delLayer(-1e3)}}),Tl=2*6378137*Math.PI/(256*2**20);function El(e){return 19-Math.log(e/Tl)/Math.LN2}function Dl(){hl.apply(this,arguments),this.maxPitch=85,this.zoomOffset=1}Dl.prototype=new hl,Dl.prototype.constructor=Dl,Dl.prototype.type=`maptalks3D`;var Ol=_l(`maptalks3D`,Dl,function(e){e.forEach(function(e){e.setCameraOption(e.model.getMaptalksCameraOption())})});function kl(e){e.registerComponentModel(xl),e.registerComponentView(wl),e.registerCoordinateSystem(`maptalks3D`,Ol),e.registerAction({type:`maptalks3DChangeCamera`,event:`maptalks3dcamerachanged`,update:`maptalks3D:updateCamera`},function(e,t){t.eachComponent({mainType:`maptalks3D`,query:e},function(t){t.setMaptalksCameraOption(e)})})}h(kl);var Al=Ea.vec3,jl=l.isDimensionStacked;function Ml(e){var t=e[0],n=e[1];return!(t>0&&n>0||t<0&&n<0)}function Nl(e,t){var n=e.getData(),r=e.get(`barSize`);if(r==null){var i=t.size,a,o,s=t.getAxis(`x`),c=t.getAxis(`y`);a=s.type===`category`?s.getBandWidth()*.7:Math.round(i[0]/Math.sqrt(n.count()))*.6,o=c.type===`category`?c.getBandWidth()*.7:Math.round(i[1]/Math.sqrt(n.count()))*.6,r=[a,o]}else F(r)||(r=[r,r]);var l=t.getAxis(`z`).scale.getExtent(),u=Ml(l),d=[`x`,`y`,`z`].map(function(t){return e.coordDimToDataDim(t)[0]}),f=jl(n,d[2]),p=f?n.getCalculationInfo(`stackResultDimension`):d[2];n.each(d,function(e,i,a,o){var s=n.get(p,o),c=f?s-a:u?0:l[0],d=t.dataToPoint([e,i,c]),m=t.dataToPoint([e,i,s]),h=Al.dist(d,m),g=[0,m[1]<d[1]?-1:1,0];Math.abs(h)===0&&(h=.1);var _=[r[0],h,r[1]];n.setItemLayout(o,[d,g,_])}),n.setLayout(`orient`,[1,0,0])}function Pl(e,t,n){for(var r=e.getDataExtent(t),i=e.getDataExtent(n),a=r[1]-r[0]||r[0],o=i[1]-i[0]||i[0],s=50,c=new Uint8Array(s*s),l=0;l<e.count();l++){var u=e.get(t,l),d=e.get(n,l),f=Math.floor((u-r[0])/a*(s-1)),p=Math.floor((d-i[0])/o*(s-1))*s+f;c[p]=c[p]||1}for(var m=0,l=0;l<c.length;l++)c[l]&&m++;return m/c.length}var Fl=Ea.vec3,Il=l.isDimensionStacked;function Ll(e,t){var n=e.getData(),r=e.get(`minHeight`)||0,i=e.get(`barSize`),a=[`lng`,`lat`,`alt`].map(function(t){return e.coordDimToDataDim(t)[0]});if(i==null){var o=t.radius*Math.PI,s=Pl(n,a[0],a[1]);i=[o/Math.sqrt(n.count()/s),o/Math.sqrt(n.count()/s)]}else F(i)||(i=[i,i]);var c=Bl(n,a);n.each(a,function(e,a,o,s){var l=n.get(c.dimension,s),u=c.isStacked?l-o:t.altitudeAxis.scale.getExtent()[0],d=Math.max(t.altitudeAxis.dataToCoord(o),r),f=t.dataToPoint([e,a,u]),p=t.dataToPoint([e,a,l]),m=Fl.sub([],p,f);Fl.normalize(m,m);var h=[i[0],d,i[1]];n.setItemLayout(s,[f,m,h])}),n.setLayout(`orient`,L.UP.array)}function Rl(e,t){var n=e.getData(),r=e.get(`barSize`),i=e.get(`minHeight`)||0,a=[`lng`,`lat`,`alt`].map(function(t){return e.coordDimToDataDim(t)[0]});if(r==null){var o=Math.min(t.size[0],t.size[2]),s=Pl(n,a[0],a[1]);r=[o/Math.sqrt(n.count()/s),o/Math.sqrt(n.count()/s)]}else F(r)||(r=[r,r]);var c=[0,1,0],l=Bl(n,a);n.each(a,function(e,a,o,s){var u=n.get(l.dimension,s),d=l.isStacked?u-o:t.altitudeAxis.scale.getExtent()[0],f=Math.max(t.altitudeAxis.dataToCoord(o),i),p=t.dataToPoint([e,a,d]),m=[r[0],f,r[1]];n.setItemLayout(s,[p,c,m])}),n.setLayout(`orient`,[1,0,0])}function zl(e,t){var n=e.getData(),r=e.coordDimToDataDim(`lng`)[0],i=e.coordDimToDataDim(`lat`)[0],a=e.coordDimToDataDim(`alt`)[0],o=e.get(`barSize`),s=e.get(`minHeight`)||0;if(o==null){var c=n.getDataExtent(r),l=n.getDataExtent(i),u=t.dataToPoint([c[0],l[0]]),d=t.dataToPoint([c[1],l[1]]),f=Math.min(Math.abs(u[0]-d[0]),Math.abs(u[1]-d[1]))||1,p=Pl(n,r,i);o=[f/Math.sqrt(n.count()/p),f/Math.sqrt(n.count()/p)]}else F(o)||(o=[o,o]),o[0]/=t.getScale()/16,o[1]/=t.getScale()/16;var m=[0,0,1],h=[r,i,a],g=Bl(n,h);n.each(h,function(e,r,i,a){var c=n.get(g.dimension,a),l=g.isStacked?c-i:0,u=t.dataToPoint([e,r,l]),d=t.dataToPoint([e,r,c]),f=Math.max(d[2]-u[2],s),p=[o[0],f,o[1]];n.setItemLayout(a,[u,m,p])}),n.setLayout(`orient`,[1,0,0])}function Bl(e,t){var n=Il(e,t[2]);return{dimension:n?e.getCalculationInfo(`stackResultDimension`):t[2],isStacked:n}}function Vl(e){e.registerLayout(function(e,t){e.eachSeriesByType(`bar3D`,function(e){var t=e.coordinateSystem,n=t&&t.type;n===`globe`?Ll(e,t):n===`cartesian3D`?Nl(e,t):n===`geo3D`?Rl(e,t):(n===`mapbox3D`||n===`maptalks3D`)&&zl(e,t)})})}var Hl={};Hl.getFormattedLabel=function(t,n,r,i,a){r=r||`normal`;var o=t.getData(i).getItemModel(n),s=t.getDataParams(n,i);a!=null&&s.value instanceof Array&&(s.value=s.value[a]);var c=o.get(r===`normal`?[`label`,`formatter`]:[`emphasis`,`label`,`formatter`]);c==null&&(c=o.get([`label`,`formatter`]));var l;return typeof c==`function`?(s.status=r,l=c(s)):typeof c==`string`&&(l=e(c,s)),l},Hl.normalizeToArray=function(e){return e instanceof Array?e:e==null?[]:[e]};function Ul(e,t){var n=[];return a(e.dimensions,function(r){var i=e.getDimensionInfo(r),a=i.otherDims[t];a!=null&&a!==!1&&(n[a]=i.name)}),n}function Wl(e,n,r){function i(e){var t=!0,i=[],s=Ul(o,`tooltip`);s.length?a(s,function(e){c(o.get(e,n),e)}):a(e,c);function c(e,n){var a=o.getDimensionInfo(n);if(!(!a||a.otherDims.tooltip===!1)){var s=a.type,c=(t?`- `+(a.tooltipName||a.name)+`: `:``)+(s===`ordinal`?e+``:s===`time`?r?``:y(`yyyy/MM/dd hh:mm:ss`,e):O(e));c&&i.push(j(c))}}return(t?`<br/>`:``)+i.join(t?`<br/>`:`, `)}var o=e.getData(),s=e.getRawValue(n),c=F(s)?i(s):j(O(s)),l=o.getName(n),u=cc(o,n);t(u)&&u.colorStops&&(u=(u.colorStops[0]||{}).color),u=u||`transparent`;var d=ee(u),f=e.name;return f===`\0-`&&(f=``),f=f?j(f)+(r?`: `:`<br/>`):``,r?d+f+c:f+d+(l?j(l)+`: `+c:c)}function Gl(e,t,r){r=r||e.getSource();var i=t||w(e.get(`coordinateSystem`))||[`x`,`y`,`z`],a=Te(r,{dimensionsDefine:r.dimensionsDefine||e.get(`dimensions`),encodeDefine:r.encodeDefine||e.get(`encode`),coordDimensions:i.map(function(t){var n=e.getReferringComponents(t+`Axis3D`).models[0];return{type:n&&n.get(`type`)===`category`?`ordinal`:`float`,name:t}})});e.get(`coordinateSystem`)===`cartesian3D`&&a.forEach(function(t){if(i.indexOf(t.coordDim)>=0){var n=e.getReferringComponents(t.coordDim+`Axis3D`).models[0];n&&n.get(`type`)===`category`&&(t.ordinalMeta=n.getOrdinalMeta())}});var o=l.enableDataStack(e,a,{byIndex:!0,stackedCoordDimension:`z`}),s=new n(a,e);return s.setCalculationInfo(o),s.initData(r),s}var Kl=u.extend({type:`series.bar3D`,dependencies:[`globe`],visualStyleAccessPathvisu:`itemStyle`,getInitialData:function(e,t){return Gl(this)},getFormattedLabel:function(e,t,n,r){var i=Hl.getFormattedLabel(this,e,t,n,r);return i==null&&(i=this.getData().get(`z`,e)),i},formatTooltip:function(e){return Wl(this,e)},defaultOption:{coordinateSystem:`cartesian3D`,globeIndex:0,grid3DIndex:0,zlevel:-10,bevelSize:0,bevelSmoothness:2,onGridPlane:`xy`,shading:`color`,minHeight:0,itemStyle:{opacity:1},label:{show:!1,distance:2,textStyle:{fontSize:14,color:`#000`,backgroundColor:`rgba(255,255,255,0.7)`,padding:3,borderRadius:3}},emphasis:{label:{show:!0}},animationDurationUpdate:500}});m(Kl.prototype,vs);var ql=Ea.vec3,Jl=Ea.mat3,Yl=Y.extend(function(){return{attributes:{position:new Y.Attribute(`position`,`float`,3,`POSITION`),normal:new Y.Attribute(`normal`,`float`,3,`NORMAL`),color:new Y.Attribute(`color`,`float`,4,`COLOR`),prevPosition:new Y.Attribute(`prevPosition`,`float`,3),prevNormal:new Y.Attribute(`prevNormal`,`float`,3)},dynamic:!0,enableNormal:!1,bevelSize:1,bevelSegments:0,_dataIndices:null,_vertexOffset:0,_triangleOffset:0}},{resetOffset:function(){this._vertexOffset=0,this._triangleOffset=0},setBarCount:function(e){var t=this.enableNormal,n=this.getBarVertexCount()*e,r=this.getBarTriangleCount()*e;this.vertexCount!==n&&(this.attributes.position.init(n),t?this.attributes.normal.init(n):this.attributes.normal.value=null,this.attributes.color.init(n)),this.triangleCount!==r&&(this.indices=n>65535?new Uint32Array(r*3):new Uint16Array(r*3),this._dataIndices=new Uint32Array(n))},getBarVertexCount:function(){var e=this.bevelSize>0?this.bevelSegments:0;return e>0?this._getBevelBarVertexCount(e):this.enableNormal?24:8},getBarTriangleCount:function(){var e=this.bevelSize>0?this.bevelSegments:0;return e>0?this._getBevelBarTriangleCount(e):12},_getBevelBarVertexCount:function(e){return(e+1)*4*(e+1)*2},_getBevelBarTriangleCount:function(e){var t=e*4+3,n=e*2+1;return(t+1)*n*2+4},setColor:function(e,t){for(var n=this.getBarVertexCount(),r=n*e,i=n*(e+1),a=r;a<i;a++)this.attributes.color.set(a,t);this.dirtyAttribute(`color`)},getDataIndexOfVertex:function(e){return this._dataIndices?this._dataIndices[e]:null},addBar:function(){for(var e=ql.create,t=ql.scaleAndAdd,n=e(),r=e(),i=e(),a=e(),o=e(),s=e(),c=e(),l=[],u=[],d=0;d<8;d++)l[d]=e();for(var f=[[0,1,5,4],[2,3,7,6],[4,5,6,7],[3,2,1,0],[0,4,7,3],[1,2,6,5]],p=[0,1,2,0,2,3],m=[],d=0;d<f.length;d++)for(var h=f[d],g=0;g<2;g++){for(var _=[],v=0;v<3;v++)_.push(h[p[g*3+v]]);m.push(_)}return function(e,d,h,g,_,v){var y=this._vertexOffset;if(this.bevelSize>0&&this.bevelSegments>0)this._addBevelBar(e,d,h,g,this.bevelSize,this.bevelSegments,_);else{ql.copy(i,d),ql.normalize(i,i),ql.cross(a,h,i),ql.normalize(a,a),ql.cross(r,i,a),ql.normalize(a,a),ql.negate(o,r),ql.negate(s,i),ql.negate(c,a),t(l[0],e,r,g[0]/2),t(l[0],l[0],a,g[2]/2),t(l[1],e,r,g[0]/2),t(l[1],l[1],c,g[2]/2),t(l[2],e,o,g[0]/2),t(l[2],l[2],c,g[2]/2),t(l[3],e,o,g[0]/2),t(l[3],l[3],a,g[2]/2),t(n,e,i,g[1]),t(l[4],n,r,g[0]/2),t(l[4],l[4],a,g[2]/2),t(l[5],n,r,g[0]/2),t(l[5],l[5],c,g[2]/2),t(l[6],n,o,g[0]/2),t(l[6],l[6],c,g[2]/2),t(l[7],n,o,g[0]/2),t(l[7],l[7],a,g[2]/2);var b=this.attributes;if(this.enableNormal){u[0]=r,u[1]=o,u[2]=i,u[3]=s,u[4]=a,u[5]=c;for(var x=this._vertexOffset,S=0;S<f.length;S++){for(var C=this._triangleOffset*3,w=0;w<6;w++)this.indices[C++]=x+p[w];x+=4,this._triangleOffset+=2}for(var S=0;S<f.length;S++)for(var T=u[S],w=0;w<4;w++){var E=f[S][w];b.position.set(this._vertexOffset,l[E]),b.normal.set(this._vertexOffset,T),b.color.set(this._vertexOffset++,_)}}else{for(var S=0;S<m.length;S++){for(var C=this._triangleOffset*3,w=0;w<3;w++)this.indices[C+w]=m[S][w]+this._vertexOffset;this._triangleOffset++}for(var S=0;S<l.length;S++)b.position.set(this._vertexOffset,l[S]),b.color.set(this._vertexOffset++,_)}}for(var D=this._vertexOffset,S=y;S<D;S++)this._dataIndices[S]=v}}(),_addBevelBar:function(){var e=ql.create(),t=ql.create(),n=ql.create(),r=Jl.create(),i=[],a=[1,-1,-1,1],o=[1,1,-1,-1],s=[2,0];return function(c,l,u,d,f,p,m){ql.copy(t,l),ql.normalize(t,t),ql.cross(n,u,t),ql.normalize(n,n),ql.cross(e,t,n),ql.normalize(n,n),r[0]=e[0],r[1]=e[1],r[2]=e[2],r[3]=t[0],r[4]=t[1],r[5]=t[2],r[6]=n[0],r[7]=n[1],r[8]=n[2],f=Math.min(d[0],d[2])/2*f;for(var h=0;h<3;h++)i[h]=Math.max(d[h]-f*2,0);for(var g=(d[0]-i[0])/2,_=(d[1]-i[1])/2,v=(d[2]-i[2])/2,y=[],b=[],x=this._vertexOffset,S=[],h=0;h<2;h++){S[h]=S[h]=[];for(var C=0;C<=p;C++)for(var w=0;w<4;w++){(C===0&&h===0||h===1&&C===p)&&S[h].push(x);for(var T=0;T<=p;T++){var E=T/p*Math.PI/2+Math.PI/2*w,D=C/p*Math.PI/2+Math.PI/2*h;b[0]=g*Math.cos(E)*Math.sin(D),b[1]=_*Math.cos(D),b[2]=v*Math.sin(E)*Math.sin(D),y[0]=b[0]+a[w]*i[0]/2,y[1]=b[1]+_+s[h]*i[1]/2,y[2]=b[2]+o[w]*i[2]/2,Math.abs(g-_)<1e-6&&Math.abs(_-v)<1e-6||(b[0]/=g*g,b[1]/=_*_,b[2]/=v*v),ql.normalize(b,b),ql.transformMat3(y,y,r),ql.transformMat3(b,b,r),ql.add(y,y,c),this.attributes.position.set(x,y),this.enableNormal&&this.attributes.normal.set(x,b),this.attributes.color.set(x,m),x++}}}for(var O=p*4+3,k=p*2+1,A=O+1,w=0;w<k;w++)for(var h=0;h<=O;h++){var j=w*A+h+this._vertexOffset,M=w*A+(h+1)%A+this._vertexOffset,N=(w+1)*A+(h+1)%A+this._vertexOffset,ee=(w+1)*A+h+this._vertexOffset;this.setTriangleIndices(this._triangleOffset++,[N,j,M]),this.setTriangleIndices(this._triangleOffset++,[N,ee,j])}this.setTriangleIndices(this._triangleOffset++,[S[0][0],S[0][2],S[0][1]]),this.setTriangleIndices(this._triangleOffset++,[S[0][0],S[0][3],S[0][2]]),this.setTriangleIndices(this._triangleOffset++,[S[1][0],S[1][1],S[1][2]]),this.setTriangleIndices(this._triangleOffset++,[S[1][0],S[1][2],S[1][3]]),this._vertexOffset=x}}()});C(Yl.prototype,Ta),C(Yl.prototype,ac);var Xl=Ea.vec3,Zl=d.extend({type:`bar3D`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this._api=t,this._labelsBuilder=new fc(256,256,t);var n=this;this._labelsBuilder.getLabelPosition=function(e,t,r){if(n._data){var i=n._data.getItemLayout(e),a=i[0],o=i[1],s=i[2][1];return Xl.scaleAndAdd([],a,o,r+s)}else return[0,0]},this._labelsBuilder.getMesh().renderOrder=100},render:function(e,t,n){var r=this._prevBarMesh;this._prevBarMesh=this._barMesh,this._barMesh=r,this._barMesh||(this._barMesh=new Q.Mesh({geometry:new Yl,shadowDepthMaterial:new Q.Material({shader:new Q.Shader(Q.Shader.source(`ecgl.sm.depth.vertex`),Q.Shader.source(`ecgl.sm.depth.fragment`))}),culling:e.coordinateSystem.type===`cartesian3D`,renderOrder:10,renderNormal:!0})),this.groupGL.remove(this._prevBarMesh),this.groupGL.add(this._barMesh),this.groupGL.add(this._labelsBuilder.getMesh());var i=e.coordinateSystem;if(this._doRender(e,n),i&&i.viewGL){i.viewGL.add(this.groupGL);var a=i.viewGL.isLinearSpace()?`define`:`undefine`;this._barMesh.material[a](`fragment`,`SRGB_DECODE`)}this._data=e.getData(),this._labelsBuilder.updateData(this._data),this._labelsBuilder.updateLabels(),this._updateAnimation(e)},_updateAnimation:function(e){Q.updateVertexAnimation([[`prevPosition`,`position`],[`prevNormal`,`normal`]],this._prevBarMesh,this._barMesh,e)},_doRender:function(e,t){var n=e.getData(),r=e.get(`shading`),i=r!==`color`,a=this,o=this._barMesh,s=`ecgl.`+r;(!o.material||o.material.shader.name!==s)&&(o.material=Q.createMaterial(s,[`VERTEX_COLOR`])),Q.setMaterialFromModel(r,o.material,e,t),o.geometry.enableNormal=i,o.geometry.resetOffset();var c=e.get(`bevelSize`),l=e.get(`bevelSmoothness`);o.geometry.bevelSegments=l,o.geometry.bevelSize=c;var u=[],d=new Float32Array(n.count()*4),f=0,p=0,m=!1;n.each(function(e){if(n.hasValue(e)){var t=cc(n,e),r=lc(n,e);r==null&&(r=1),Q.parseColor(t,u),u[3]*=r,d[f++]=u[0],d[f++]=u[1],d[f++]=u[2],d[f++]=u[3],u[3]>0&&(p++,u[3]<.99&&(m=!0))}}),o.geometry.setBarCount(p);var h=n.getLayout(`orient`),g=this._barIndexOfData=new Int32Array(n.count()),p=0;n.each(function(e){if(!n.hasValue(e)){g[e]=-1;return}var t=n.getItemLayout(e),r=t[0],i=t[1],o=t[2],s=e*4;u[0]=d[s++],u[1]=d[s++],u[2]=d[s++],u[3]=d[s++],u[3]>0&&(a._barMesh.geometry.addBar(r,i,h,o,u,e),g[e]=p++)}),o.geometry.dirty(),o.geometry.updateBoundingBox();var _=o.material;_.transparent=m,_.depthMask=!m,o.geometry.sortTriangles=m,this._initHandler(e,t)},_initHandler:function(e,t){var n=e.getData(),r=this._barMesh,i=e.coordinateSystem.type===`cartesian3D`;r.seriesIndex=e.seriesIndex;var a=-1;r.off(`mousemove`),r.off(`mouseout`),r.on(`mousemove`,function(e){var o=r.geometry.getDataIndexOfVertex(e.triangle[0]);o!==a&&(this._downplay(a),this._highlight(o),this._labelsBuilder.updateLabels([o]),i&&t.dispatchAction({type:`grid3DShowAxisPointer`,value:[n.get(`x`,o),n.get(`y`,o),n.get(`z`,o,!0)]})),a=o,r.dataIndex=o},this),r.on(`mouseout`,function(e){this._downplay(a),this._labelsBuilder.updateLabels(),a=-1,r.dataIndex=-1,i&&t.dispatchAction({type:`grid3DHideAxisPointer`})},this)},_highlight:function(e){var t=this._data;if(t){var n=this._barIndexOfData[e];if(!(n<0)){var r=t.getItemModel(e).getModel(`emphasis.itemStyle`),i=r.get(`color`),a=r.get(`opacity`);i==null&&(i=de(cc(t,e),-.4)),a==null&&(a=lc(t,e));var o=Q.parseColor(i);o[3]*=a,this._barMesh.geometry.setColor(n,o),this._api.getZr().refresh()}}},_downplay:function(e){var t=this._data;if(t){var n=this._barIndexOfData[e];if(!(n<0)){var r=cc(t,e),i=lc(t,e),a=Q.parseColor(r);a[3]*=i,this._barMesh.geometry.setColor(n,a),this._api.getZr().refresh()}}},highlight:function(e,t,n,r){this._toggleStatus(`highlight`,e,t,n,r)},downplay:function(e,t,n,r){this._toggleStatus(`downplay`,e,t,n,r)},_toggleStatus:function(e,t,n,r,i){var o=t.getData(),s=X.queryDataIndex(o,i),c=this;s==null?o.each(function(t){e===`highlight`?c._highlight(t):c._downplay(t)}):a(Hl.normalizeToArray(s),function(t){e===`highlight`?this._highlight(t):this._downplay(t)},this)},remove:function(){this.groupGL.removeAll()},dispose:function(){this._labelsBuilder.dispose(),this.groupGL.removeAll()}});function Ql(e){e.registerChartView(Zl),e.registerSeriesModel(Kl),Vl(e),e.registerProcessor(function(e,t){e.eachSeriesByType(`bar3d`,function(e){var t=e.getData();t.filterSelf(function(e){return t.hasValue(e)})})})}h(Ql);var $l=u.extend({type:`series.line3D`,dependencies:[`grid3D`],visualStyleAccessPath:`lineStyle`,visualDrawType:`stroke`,getInitialData:function(e,t){return Gl(this)},formatTooltip:function(e){return Wl(this,e)},defaultOption:{coordinateSystem:`cartesian3D`,zlevel:-10,grid3DIndex:0,lineStyle:{width:2},animationDurationUpdate:500}}),eu=Ea.vec3;Q.Shader.import(Ka);var tu=d.extend({type:`line3D`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this._api=t},render:function(e,t,n){var r=this._prevLine3DMesh;this._prevLine3DMesh=this._line3DMesh,this._line3DMesh=r,this._line3DMesh||(this._line3DMesh=new Q.Mesh({geometry:new ka({useNativeLine:!1,sortTriangles:!0}),material:new Q.Material({shader:Q.createShader(`ecgl.meshLines3D`)}),renderOrder:10}),this._line3DMesh.geometry.pick=this._pick.bind(this)),this.groupGL.remove(this._prevLine3DMesh),this.groupGL.add(this._line3DMesh);var i=e.coordinateSystem;if(i&&i.viewGL){i.viewGL.add(this.groupGL);var a=i.viewGL.isLinearSpace()?`define`:`undefine`;this._line3DMesh.material[a](`fragment`,`SRGB_DECODE`)}this._doRender(e,n),this._data=e.getData(),this._camera=i.viewGL.camera,this.updateCamera(),this._updateAnimation(e)},updateCamera:function(){this._updateNDCPosition()},_doRender:function(e,t){var n=e.getData(),r=this._line3DMesh;r.geometry.resetOffset();var i=n.getLayout(`points`),a=[],o=new Float32Array(i.length/3*4),s=0,c=!1;n.each(function(e){var t=cc(n,e),r=lc(n,e);r==null&&(r=1),Q.parseColor(t,a),a[3]*=r,o[s++]=a[0],o[s++]=a[1],o[s++]=a[2],o[s++]=a[3],a[3]<.99&&(c=!0)}),r.geometry.setVertexCount(r.geometry.getPolylineVertexCount(i)),r.geometry.setTriangleCount(r.geometry.getPolylineTriangleCount(i)),r.geometry.addPolyline(i,o,X.firstNotNull(e.get(`lineStyle.width`),1)),r.geometry.dirty(),r.geometry.updateBoundingBox();var l=r.material;l.transparent=c,l.depthMask=!c;var u=e.getModel(`debug.wireframe`);u.get(`show`)?(r.geometry.createAttribute(`barycentric`,`float`,3),r.geometry.generateBarycentric(),r.material.set(`both`,`WIREFRAME_TRIANGLE`),r.material.set(`wireframeLineColor`,Q.parseColor(u.get(`lineStyle.color`)||`rgba(0,0,0,0.5)`)),r.material.set(`wireframeLineWidth`,X.firstNotNull(u.get(`lineStyle.width`),1))):r.material.set(`both`,`WIREFRAME_TRIANGLE`),this._points=i,this._initHandler(e,t)},_updateAnimation:function(e){Q.updateVertexAnimation([[`prevPosition`,`position`],[`prevPositionPrev`,`positionPrev`],[`prevPositionNext`,`positionNext`]],this._prevLine3DMesh,this._line3DMesh,e)},_initHandler:function(e,t){var n=e.getData(),r=e.coordinateSystem,i=this._line3DMesh,a=-1;i.seriesIndex=e.seriesIndex,i.off(`mousemove`),i.off(`mouseout`),i.on(`mousemove`,function(o){var s=r.pointToData(o.point.array),c=e.indicesOfNearest?e.indicesOfNearest(`x`,`x`,s[0])[0]:n.indicesOfNearest(`x`,s[0])[0];c!==a&&(t.dispatchAction({type:`grid3DShowAxisPointer`,value:[n.get(`x`,c),n.get(`y`,c),n.get(`z`,c)]}),i.dataIndex=c),a=c},this),i.on(`mouseout`,function(e){a=-1,i.dataIndex=-1,t.dispatchAction({type:`grid3DHideAxisPointer`})},this)},_updateNDCPosition:function(){var e=new H,t=this._camera;H.multiply(e,t.projectionMatrix,t.viewMatrix);var n=this._positionNDC,r=this._points,i=r.length/3;(!n||n.length/2!==i)&&(n=this._positionNDC=new Float32Array(i*2));for(var a=[],o=0;o<i;o++){var s=o*3,c=o*2;a[0]=r[s],a[1]=r[s+1],a[2]=r[s+2],a[3]=1,eu.transformMat4(a,a,e.array),n[c]=a[0]/a[3],n[c+1]=a[1]/a[3]}},_pick:function(e,t,n,r,i,a){var o=this._positionNDC,s=this._data.hostModel.get(`lineStyle.width`),c=-1,l=n.viewport.width,u=n.viewport.height,d=l*.5,f=u*.5;e=(e+1)*d,t=(t+1)*f;for(var p=1;p<o.length/2;p++){var m=(o[(p-1)*2]+1)*d,h=(o[(p-1)*2+1]+1)*f,g=(o[p*2]+1)*d,_=(o[p*2+1]+1)*f;ue(m,h,g,_,s,e,t)&&(c=(m-e)*(m-e)+(h-t)*(h-t)<(g-e)*(g-e)+(_-t)*(_-t)?p-1:p)}if(c>=0){var v=c*3,y=new L(this._points[v],this._points[v+1],this._points[v+2]);a.push({dataIndex:c,point:y,pointWorld:y.clone(),target:this._line3DMesh,distance:this._camera.getWorldPosition().dist(y)})}},remove:function(){this.groupGL.removeAll()},dispose:function(){this.groupGL.removeAll()}});function nu(e){e.registerChartView(tu),e.registerSeriesModel($l),e.registerLayout(function(e,t){e.eachSeriesByType(`line3D`,function(e){var t=e.getData(),n=e.coordinateSystem;if(n){if(n.type!==`cartesian3D`)return;var r=new Float32Array(t.count()*3),i=[],a=[],o=n.dimensions.map(function(t){return e.coordDimToDataDim(t)[0]});n&&t.each(o,function(e,t,o,s){i[0]=e,i[1]=t,i[2]=o,n.dataToPoint(i,a),r[s*3]=a[0],r[s*3+1]=a[1],r[s*3+2]=a[2]}),t.setLayout(`points`,r)}})})}h(nu);var ru=u.extend({type:`series.scatter3D`,dependencies:[`globe`,`grid3D`,`geo3D`],visualStyleAccessPath:`itemStyle`,hasSymbolVisual:!0,getInitialData:function(e,t){return Gl(this)},getFormattedLabel:function(e,t,n,r){var i=Hl.getFormattedLabel(this,e,t,n,r);if(i==null){var a=this.getData(),o=a.dimensions[a.dimensions.length-1];i=a.get(o,e)}return i},formatTooltip:function(e){return Wl(this,e)},defaultOption:{coordinateSystem:`cartesian3D`,zlevel:-10,progressive:1e5,progressiveThreshold:1e5,grid3DIndex:0,globeIndex:0,symbol:`circle`,symbolSize:10,blendMode:`source-over`,label:{show:!1,position:`right`,distance:5,textStyle:{fontSize:14,color:`#000`,backgroundColor:`rgba(255,255,255,0.7)`,padding:3,borderRadius:3}},itemStyle:{opacity:.8},emphasis:{label:{show:!0}},animationDurationUpdate:500}});function iu(e,t,n){var t=t||document.createElement(`canvas`);t.width=e,t.height=e;var r=t.getContext(`2d`);return n&&n(r),t}function au(e,t,n,r){F(t)||(t=[t,t]);var i=su.getMarginByStyle(n,r),a=t[0]+i.left+i.right,o=t[1]+i.top+i.bottom,c=s(e,0,0,t[0],t[1]),l=Math.max(a,o);c.x=i.left,c.y=i.top,a>o?c.y+=(l-o)/2:c.x+=(l-a)/2;var u=c.getBoundingRect();return c.x-=u.x,c.y-=u.y,c.setStyle(n),c.update(),c.__size=l,c}function ou(e,t,n){var r=t.width,i=t.height,a=e.canvas.width,o=e.canvas.height,s=r/a,c=i/o;function l(e){return e<128?1:-1}function u(e,a){var o=1/0;e=Math.floor(e*s),a=Math.floor(a*c);for(var u=a*r+e,d=t.data[u*4],f=l(d),p=Math.max(a-n,0);p<Math.min(a+n,i);p++)for(var m=Math.max(e-n,0);m<Math.min(e+n,r);m++){var u=p*r+m,h=t.data[u*4],g=l(h),_=m-e,v=p-a;if(f!==g){var y=_*_+v*v;y<o&&(o=y)}}return f*Math.sqrt(o)}for(var d=e.createImageData(a,o),f=0;f<o;f++)for(var p=0;p<a;p++){var m=u(p,f)/n*.5+.5,h=(f*a+p)*4;d.data[h++]=(1-m)*255,d.data[h++]=(1-m)*255,d.data[h++]=(1-m)*255,d.data[h++]=255}return d}var su={getMarginByStyle:function(e){var t=e.minMargin||0,n=0;e.stroke&&e.stroke!==`none`&&(n=e.lineWidth==null?1:e.lineWidth);var r=e.shadowBlur||0,i=e.shadowOffsetX||0,a=e.shadowOffsetY||0,o={};return o.left=Math.max(n/2,-i+r,t),o.right=Math.max(n/2,i+r,t),o.top=Math.max(n/2,-a+r,t),o.bottom=Math.max(n/2,a+r,t),o},createSymbolSprite:function(e,t,n,r){var i=au(e,t,n),a=su.getMarginByStyle(n);return{image:iu(i.__size,r,function(e){T(e,i)}),margin:a}},createSDFFromCanvas:function(e,t,n,r){return iu(t,r,function(t){var r=e.getContext(`2d`).getImageData(0,0,e.width,e.height);t.putImageData(ou(t,r,n),0,0)})},createSimpleSprite:function(e,t){return iu(e,t,function(t){var n=e/2;t.beginPath(),t.arc(n,n,60,0,Math.PI*2,!1),t.closePath();var r=t.createRadialGradient(n,n,0,n,n,n);r.addColorStop(0,`rgba(255, 255, 255, 1)`),r.addColorStop(.5,`rgba(255, 255, 255, 0.5)`),r.addColorStop(1,`rgba(255, 255, 255, 0)`),t.fillStyle=r,t.fill()})}},cu=Ea.vec3,lu={needsSortVertices:function(){return this.sortVertices},needsSortVerticesProgressively:function(){return this.needsSortVertices()&&this.vertexCount>=2e4},doSortVertices:function(e,t){var n=this.indices,r=cu.create();if(!n){n=this.indices=this.vertexCount>65535?new Uint32Array(this.vertexCount):new Uint16Array(this.vertexCount);for(var i=0;i<n.length;i++)n[i]=i}if(t===0){var a=this.attributes.position,e=e.array,o=0;(!this._zList||this._zList.length!==this.vertexCount)&&(this._zList=new Float32Array(this.vertexCount));for(var s,i=0;i<this.vertexCount;i++){a.get(i,r);var c=cu.sqrDist(r,e);isNaN(c)&&(c=1e7,o++),i===0?(s=c,c=0):c-=s,this._zList[i]=c}this._noneCount=o}if(this.vertexCount<2e4)t===0&&this._simpleSort(this._noneCount/this.vertexCount>.05);else for(var i=0;i<3;i++)this._progressiveQuickSort(t*3+i);this.dirtyIndices()},_simpleSort:function(e){var t=this._zList,n=this.indices;function r(e,n){return t[n]-t[e]}e?Array.prototype.sort.call(n,r):ec.sort(n,r,0,n.length-1)},_progressiveQuickSort:function(e){var t=this._zList,n=this.indices;this._quickSort=this._quickSort||new ec,this._quickSort.step(n,function(e,n){return t[n]-t[e]},e)}},uu=`@export ecgl.sdfSprite.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform float elapsedTime : 0;

attribute vec3 position : POSITION;

#ifdef VERTEX_SIZE
attribute float size;
#else
uniform float u_Size;
#endif

#ifdef VERTEX_COLOR
attribute vec4 a_FillColor: COLOR;
varying vec4 v_Color;
#endif

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
attribute float prevSize;
uniform float percent : 1.0;
#endif


#ifdef POSITIONTEXTURE_ENABLED
uniform sampler2D positionTexture;
#endif

varying float v_Size;

void main()
{

#ifdef POSITIONTEXTURE_ENABLED
 gl_Position = worldViewProjection * vec4(texture2D(positionTexture, position.xy).xy, -10.0, 1.0);
#else

 #ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
 #else
 vec3 pos = position;
 #endif
 gl_Position = worldViewProjection * vec4(pos, 1.0);
#endif

#ifdef VERTEX_SIZE
#ifdef VERTEX_ANIMATION
 v_Size = mix(prevSize, size, percent);
#else
 v_Size = size;
#endif
#else
 v_Size = u_Size;
#endif

#ifdef VERTEX_COLOR
 v_Color = a_FillColor;
 #endif

 gl_PointSize = v_Size;
}

@end

@export ecgl.sdfSprite.fragment

uniform vec4 color: [1, 1, 1, 1];
uniform vec4 strokeColor: [1, 1, 1, 1];
uniform float smoothing: 0.07;

uniform float lineWidth: 0.0;

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif

varying float v_Size;

uniform sampler2D sprite;

@import clay.util.srgb

void main()
{
 gl_FragColor = color;

 vec4 _strokeColor = strokeColor;

#ifdef VERTEX_COLOR
 gl_FragColor *= v_Color;
 #endif

#ifdef SPRITE_ENABLED
 float d = texture2D(sprite, gl_PointCoord).r;
 gl_FragColor.a *= smoothstep(0.5 - smoothing, 0.5 + smoothing, d);

 if (lineWidth > 0.0) {
 float sLineWidth = lineWidth / 2.0;

 float outlineMaxValue0 = 0.5 + sLineWidth;
 float outlineMaxValue1 = 0.5 + sLineWidth + smoothing;
 float outlineMinValue0 = 0.5 - sLineWidth - smoothing;
 float outlineMinValue1 = 0.5 - sLineWidth;

 if (d <= outlineMaxValue1 && d >= outlineMinValue0) {
 float a = _strokeColor.a;
 if (d <= outlineMinValue1) {
 a = a * smoothstep(outlineMinValue0, outlineMinValue1, d);
 }
 else {
 a = a * smoothstep(outlineMaxValue1, outlineMaxValue0, d);
 }
 gl_FragColor.rgb = mix(gl_FragColor.rgb * gl_FragColor.a, _strokeColor.rgb, a);
 gl_FragColor.a = gl_FragColor.a * (1.0 - a) + a;
 }
 }
#endif

#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(gl_FragColor);
#endif
}
@end`,du=Ea.vec4;Q.Shader.import(uu);var fu=Q.Mesh.extend(function(){var e=new Q.Geometry({dynamic:!0,attributes:{color:new Q.Geometry.Attribute(`color`,`float`,4,`COLOR`),position:new Q.Geometry.Attribute(`position`,`float`,3,`POSITION`),size:new Q.Geometry.Attribute(`size`,`float`,1),prevPosition:new Q.Geometry.Attribute(`prevPosition`,`float`,3),prevSize:new Q.Geometry.Attribute(`prevSize`,`float`,1)}});Object.assign(e,lu);var t=new Q.Material({shader:Q.createShader(`ecgl.sdfSprite`),transparent:!0,depthMask:!1});t.enableTexture(`sprite`),t.define(`both`,`VERTEX_COLOR`),t.define(`both`,`VERTEX_SIZE`);var n=new Q.Texture2D({image:document.createElement(`canvas`),flipY:!1});return t.set(`sprite`,n),e.pick=this._pick.bind(this),{geometry:e,material:t,mode:Q.Mesh.POINTS,sizeScale:1}},{_pick:function(e,t,n,r,i,a){var o=this._positionNDC;if(o)for(var s=n.viewport,c=2/s.width,l=2/s.height,u=this.geometry.vertexCount-1;u>=0;u--){var d=this.geometry.indices?this.geometry.indices[u]:u,f=o[d*2],p=o[d*2+1],m=this.geometry.attributes.size.get(d)/this.sizeScale/2;if(e>f-m*c&&e<f+m*c&&t>p-m*l&&t<p+m*l){var h=new Q.Vector3,g=new Q.Vector3;this.geometry.attributes.position.get(d,h.array),Q.Vector3.transformMat4(g,h,this.worldTransform),a.push({vertexIndex:d,point:h,pointWorld:g,target:this,distance:g.distance(r.getWorldPosition())})}}},updateNDCPosition:function(e,t,n){var r=this._positionNDC,i=this.geometry;(!r||r.length/2!==i.vertexCount)&&(r=this._positionNDC=new Float32Array(i.vertexCount*2));for(var a=du.create(),o=0;o<i.vertexCount;o++)i.attributes.position.get(o,a),a[3]=1,du.transformMat4(a,a,e.array),du.scale(a,a,1/a[3]),r[o*2]=a[0],r[o*2+1]=a[1]}}),pu=20,mu=-10;function hu(e,t){return e&&t&&e[0]===t[0]&&e[1]===t[1]}function gu(e,t){this.rootNode=new Q.Node,this.is2D=e,this._labelsBuilder=new fc(256,256,t),this._labelsBuilder.getMesh().renderOrder=100,this.rootNode.add(this._labelsBuilder.getMesh()),this._api=t,this._spriteImageCanvas=document.createElement(`canvas`),this._startDataIndex=0,this._endDataIndex=0,this._sizeScale=1}gu.prototype={constructor:gu,highlightOnMouseover:!0,update:function(e,t,n,r,i){var a=this._prevMesh;this._prevMesh=this._mesh,this._mesh=a;var o=e.getData();if(r==null&&(r=0),i==null&&(i=o.count()),this._startDataIndex=r,this._endDataIndex=i-1,!this._mesh){var s=this._prevMesh&&this._prevMesh.material;this._mesh=new fu({renderOrder:10,frustumCulling:!1}),s&&(this._mesh.material=s)}var s=this._mesh.material,c=this._mesh.geometry,l=c.attributes;this.rootNode.remove(this._prevMesh),this.rootNode.add(this._mesh),this._setPositionTextureToMesh(this._mesh,this._positionTexture);var u=this._getSymbolInfo(e,r,i),d=n.getDevicePixelRatio(),f=e.getModel(`itemStyle`).getItemStyle(),p=e.get(`large`),m=1;u.maxSize>2?(m=this._updateSymbolSprite(e,f,u,d),s.enableTexture(`sprite`)):s.disableTexture(`sprite`),l.position.init(i-r);var h=[];if(p){s.undefine(`VERTEX_SIZE`),s.undefine(`VERTEX_COLOR`);var g=oc(o),_=sc(o);Q.parseColor(g,h),h[3]*=_,s.set({color:h,u_Size:u.maxSize*this._sizeScale})}else s.set({color:[1,1,1,1]}),s.define(`VERTEX_SIZE`),s.define(`VERTEX_COLOR`),l.size.init(i-r),l.color.init(i-r),this._originalOpacity=new Float32Array(i-r);for(var v=o.getLayout(`points`),y=l.position.value,b=0;b<i-r;b++){var x=b*3,S=b*2;if(this.is2D?(y[x]=v[S],y[x+1]=v[S+1],y[x+2]=mu):(y[x]=v[x],y[x+1]=v[x+1],y[x+2]=v[x+2]),!p){var g=cc(o,b),_=lc(o,b);Q.parseColor(g,h),h[3]*=_,l.color.set(b,h),h[3];var C=o.getItemVisual(b,`symbolSize`);C=C instanceof Array?Math.max(C[0],C[1]):C,isNaN(C)&&(C=0),l.size.value[b]=C*m*this._sizeScale,this._originalOpacity[b]=h[3]}}this._mesh.sizeScale=m,c.updateBoundingBox(),c.dirty(),this._updateMaterial(e,f);var w=e.coordinateSystem;w&&w.viewGL&&s[w.viewGL.isLinearSpace()?`define`:`undefine`](`fragment`,`SRGB_DECODE`),p||this._updateLabelBuilder(e,r,i),this._updateHandler(e,t,n),this._updateAnimation(e),this._api=n},getPointsMesh:function(){return this._mesh},updateLabels:function(e){this._labelsBuilder.updateLabels(e)},hideLabels:function(){this.rootNode.remove(this._labelsBuilder.getMesh())},showLabels:function(){this.rootNode.add(this._labelsBuilder.getMesh())},dispose:function(){this._labelsBuilder.dispose()},_updateSymbolSprite:function(e,t,n,r){n.maxSize=Math.min(n.maxSize*2,200);var i=[];return n.aspect>1?(i[0]=n.maxSize,i[1]=n.maxSize/n.aspect):(i[1]=n.maxSize,i[0]=n.maxSize*n.aspect),i[0]=i[0]||1,i[1]=i[1]||1,(this._symbolType!==n.type||!hu(this._symbolSize,i)||this._lineWidth!==t.lineWidth)&&(su.createSymbolSprite(n.type,i,{fill:`#fff`,lineWidth:t.lineWidth,stroke:`transparent`,shadowColor:`transparent`,minMargin:Math.min(i[0]/2,10)},this._spriteImageCanvas),su.createSDFFromCanvas(this._spriteImageCanvas,Math.min(this._spriteImageCanvas.width,32),pu,this._mesh.material.get(`sprite`).image),this._symbolType=n.type,this._symbolSize=i,this._lineWidth=t.lineWidth),this._spriteImageCanvas.width/n.maxSize*r},_updateMaterial:function(e,t){var n=e.get(`blendMode`)===`lighter`?Q.additiveBlend:null,r=this._mesh.material;r.blend=n,r.set(`lineWidth`,t.lineWidth/pu);var i=Q.parseColor(t.stroke);r.set(`strokeColor`,i),r.transparent=!0,r.depthMask=!1,r.depthTest=!this.is2D,r.sortVertices=!this.is2D},_updateLabelBuilder:function(e,t,n){var r=e.getData(),i=this._mesh.geometry,a=i.attributes.position.value,t=this._startDataIndex,o=this._mesh.sizeScale;this._labelsBuilder.updateData(r,t,n),this._labelsBuilder.getLabelPosition=function(e,n,r){var i=(e-t)*3;return[a[i],a[i+1],a[i+2]]},this._labelsBuilder.getLabelDistance=function(e,n,r){return i.attributes.size.get(e-t)/o/2+r},this._labelsBuilder.updateLabels()},_updateAnimation:function(e){Q.updateVertexAnimation([[`prevPosition`,`position`],[`prevSize`,`size`]],this._prevMesh,this._mesh,e)},_updateHandler:function(e,t,n){var r=e.getData(),i=this._mesh,a=this,o=-1,s=e.coordinateSystem&&e.coordinateSystem.type===`cartesian3D`,c;s&&(c=e.coordinateSystem.model),i.seriesIndex=e.seriesIndex,i.off(`mousemove`),i.off(`mouseout`),i.on(`mousemove`,function(t){var l=t.vertexIndex+a._startDataIndex;l!==o&&(this.highlightOnMouseover&&(this.downplay(r,o),this.highlight(r,l),this._labelsBuilder.updateLabels([l])),s&&n.dispatchAction({type:`grid3DShowAxisPointer`,value:[r.get(e.coordDimToDataDim(`x`)[0],l),r.get(e.coordDimToDataDim(`y`)[0],l),r.get(e.coordDimToDataDim(`z`)[0],l)],grid3DIndex:c.componentIndex})),i.dataIndex=l,o=l},this),i.on(`mouseout`,function(e){var t=e.vertexIndex+a._startDataIndex;this.highlightOnMouseover&&(this.downplay(r,t),this._labelsBuilder.updateLabels()),o=-1,i.dataIndex=-1,s&&n.dispatchAction({type:`grid3DHideAxisPointer`,grid3DIndex:c.componentIndex})},this)},updateLayout:function(e,t,n){var r=e.getData();if(this._mesh){var i=this._mesh.geometry.attributes.position.value,a=r.getLayout(`points`);if(this.is2D)for(var o=0;o<a.length/2;o++){var s=o*3,c=o*2;i[s]=a[c],i[s+1]=a[c+1],i[s+2]=mu}else for(var o=0;o<a.length;o++)i[o]=a[o];this._mesh.geometry.dirty(),n.getZr().refresh()}},updateView:function(e){if(this._mesh){var t=new H;H.mul(t,e.viewMatrix,this._mesh.worldTransform),H.mul(t,e.projectionMatrix,t),this._mesh.updateNDCPosition(t,this.is2D,this._api)}},highlight:function(e,t){if(!(t>this._endDataIndex||t<this._startDataIndex)){var n=e.getItemModel(t).getModel(`emphasis.itemStyle`),r=n.get(`color`),i=n.get(`opacity`);r==null&&(r=de(cc(e,t),-.4)),i==null&&(i=lc(e,t));var a=Q.parseColor(r);a[3]*=i,this._mesh.geometry.attributes.color.set(t-this._startDataIndex,a),this._mesh.geometry.dirtyAttribute(`color`),this._api.getZr().refresh()}},downplay:function(e,t){if(!(t>this._endDataIndex||t<this._startDataIndex)){var n=cc(e,t),r=lc(e,t),i=Q.parseColor(n);i[3]*=r,this._mesh.geometry.attributes.color.set(t-this._startDataIndex,i),this._mesh.geometry.dirtyAttribute(`color`),this._api.getZr().refresh()}},fadeOutAll:function(e){if(this._originalOpacity){for(var t=this._mesh.geometry,n=0;n<t.vertexCount;n++){var r=this._originalOpacity[n]*e;t.attributes.color.value[n*4+3]=r}t.dirtyAttribute(`color`),this._api.getZr().refresh()}},fadeInAll:function(){this.fadeOutAll(1)},setPositionTexture:function(e){this._mesh&&this._setPositionTextureToMesh(this._mesh,e),this._positionTexture=e},removePositionTexture:function(){this._positionTexture=null,this._mesh&&this._setPositionTextureToMesh(this._mesh,null)},setSizeScale:function(e){if(e!==this._sizeScale){if(this._mesh){var t=this._mesh.material.get(`u_Size`);this._mesh.material.set(`u_Size`,t/this._sizeScale*e);var n=this._mesh.geometry.attributes;if(n.size.value)for(var r=0;r<n.size.value.length;r++)n.size.value[r]=n.size.value[r]/this._sizeScale*e}this._sizeScale=e}},_setPositionTextureToMesh:function(e,t){t&&e.material.set(`positionTexture`,t),e.material[t?`enableTexture`:`disableTexture`](`positionTexture`)},_getSymbolInfo:function(e,t,n){if(e.get(`large`)){var r=X.firstNotNull(e.get(`symbolSize`),1),i,a;return r instanceof Array?(i=Math.max(r[0],r[1]),a=r[0]/r[1]):(i=r,a=1),{maxSize:r,type:e.get(`symbol`),aspect:a}}for(var o=e.getData(),a,s=o.getItemVisual(0,`symbol`)||`circle`,i=0,c=t;c<n;c++){var r=o.getItemVisual(c,`symbolSize`),l=o.getItemVisual(c,`symbol`),u;if(r instanceof Array)u=r[0]/r[1],i=Math.max(Math.max(r[0],r[1]),i);else{if(isNaN(r))continue;u=1,i=Math.max(r,i)}s=l,a=u}return{maxSize:i,type:s,aspect:a}}};var _u=d.extend({type:`scatter3D`,hasSymbolVisual:!0,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this._pointsBuilderList=[],this._currentStep=0},render:function(e,t,n){if(this.groupGL.removeAll(),e.getData().count()){var r=e.coordinateSystem;if(r&&r.viewGL){r.viewGL.add(this.groupGL),this._camera=r.viewGL.camera;var i=this._pointsBuilderList[0];i||(i=this._pointsBuilderList[0]=new gu(!1,n)),this._pointsBuilderList.length=1,this.groupGL.add(i.rootNode),i.update(e,t,n),i.updateView(r.viewGL.camera)}}},incrementalPrepareRender:function(e,t,n){var r=e.coordinateSystem;r&&r.viewGL&&(r.viewGL.add(this.groupGL),this._camera=r.viewGL.camera),this.groupGL.removeAll(),this._currentStep=0},incrementalRender:function(e,t,n,r){if(!(e.end<=e.start)){var i=this._pointsBuilderList[this._currentStep];i||(i=new gu(!1,r),this._pointsBuilderList[this._currentStep]=i),this.groupGL.add(i.rootNode),i.update(t,n,r,e.start,e.end),i.updateView(t.coordinateSystem.viewGL.camera),this._currentStep++}},updateCamera:function(){this._pointsBuilderList.forEach(function(e){e.updateView(this._camera)},this)},highlight:function(e,t,n,r){this._toggleStatus(`highlight`,e,t,n,r)},downplay:function(e,t,n,r){this._toggleStatus(`downplay`,e,t,n,r)},_toggleStatus:function(e,t,n,r,i){var o=t.getData(),s=X.queryDataIndex(o,i),c=e===`highlight`;s==null?o.each(function(e){for(var t=0;t<this._pointsBuilderList.length;t++){var n=this._pointsBuilderList[t];c?n.highlight(o,e):n.downplay(o,e)}}):a(Hl.normalizeToArray(s),function(e){for(var t=0;t<this._pointsBuilderList.length;t++){var n=this._pointsBuilderList[t];c?n.highlight(o,e):n.downplay(o,e)}},this)},dispose:function(){this._pointsBuilderList.forEach(function(e){e.dispose()}),this.groupGL.removeAll()},remove:function(){this.groupGL.removeAll()}});function vu(e){e.registerChartView(_u),e.registerSeriesModel(ru),e.registerLayout({seriesType:`scatter3D`,reset:function(e){var t=e.coordinateSystem;if(t){var n=t.dimensions;if(n.length<3)return;var r=n.map(function(t){return e.coordDimToDataDim(t)[0]}),i=[],a=[];return{progress:function(e,n){for(var o=new Float32Array((e.end-e.start)*3),s=e.start;s<e.end;s++){var c=(s-e.start)*3;i[0]=n.get(r[0],s),i[1]=n.get(r[1],s),i[2]=n.get(r[2],s),t.dataToPoint(i,a),o[c]=a[0],o[c+1]=a[1],o[c+2]=a[2]}n.setLayout(`points`,o)}}}}})}h(vu);var yu=Ea.vec3,bu=Ea.vec2,xu=yu.normalize,Su=yu.cross,Cu=yu.sub,wu=yu.add,Tu=yu.create,Eu=Tu(),Du=Tu(),Ou=Tu(),ku=Tu(),Au=[],ju=[];function Mu(e,t){bu.copy(Au,e[0]),bu.copy(ju,e[1]);var n=[],r=n[0]=Tu(),i=n[1]=Tu(),a=n[2]=Tu(),o=n[3]=Tu();t.dataToPoint(Au,r),t.dataToPoint(ju,o),xu(Eu,r),Cu(Du,o,r),xu(Du,Du),Su(Ou,Du,Eu),xu(Ou,Ou),Su(Du,Eu,Ou),wu(i,Eu,Du),xu(i,i),xu(Eu,o),Cu(Du,r,o),xu(Du,Du),Su(Ou,Du,Eu),xu(Ou,Ou),Su(Du,Eu,Ou),wu(a,Eu,Du),xu(a,a),wu(ku,r,o),xu(ku,ku);var s=yu.dot(r,ku),c=yu.dot(ku,i),l=(Math.max(yu.len(r),yu.len(o))-s)/c*2;return yu.scaleAndAdd(i,r,i,l),yu.scaleAndAdd(a,o,a,l),n}function Nu(e,t,n){var r=[],i=r[0]=yu.create(),a=r[1]=yu.create(),o=r[2]=yu.create(),s=r[3]=yu.create();t.dataToPoint(e[0],i),t.dataToPoint(e[1],s);var c=yu.dist(i,s);return yu.lerp(a,i,s,.3),yu.lerp(o,i,s,.3),yu.scaleAndAdd(a,a,n,Math.min(c*.1,10)),yu.scaleAndAdd(o,o,n,Math.min(c*.1,10)),r}function Pu(e,t){for(var n=new Float32Array(e.length*3),r=0,i=[],a=0;a<e.length;a++)t.dataToPoint(e[a],i),n[r++]=i[0],n[r++]=i[1],n[r++]=i[2];return n}function Fu(e){var t=[];return e.each(function(n){var r=e.getItemModel(n),i=r.option instanceof Array?r.option:r.getShallow(`coords`,!0);t.push(i)}),{coordsList:t}}function Iu(e,t){var n=e.getData(),r=e.get(`polyline`);n.setLayout(`lineType`,r?`polyline`:`cubicBezier`);var i=Fu(n);n.each(function(e){var a=i.coordsList[e],o=r?Pu:Mu;n.setItemLayout(e,o(a,t))})}function Lu(e,t,n){var r=e.getData(),i=e.get(`polyline`),a=Fu(r);r.setLayout(`lineType`,i?`polyline`:`cubicBezier`),r.each(function(e){var o=a.coordsList[e],s=i?Pu(o,t):Nu(o,t,n);r.setItemLayout(e,s)})}function Ru(e,t){e.eachSeriesByType(`lines3D`,function(e){var t=e.coordinateSystem;t.type===`globe`?Iu(e,t):t.type===`geo3D`?Lu(e,t,[0,1,0]):(t.type===`mapbox3D`||t.type===`maptalks3D`)&&Lu(e,t,[0,0,1])})}var zu=u.extend({type:`series.lines3D`,dependencies:[`globe`],visualStyleAccessPath:`lineStyle`,visualDrawType:`stroke`,getInitialData:function(e,t){var r=new n([`value`],this);return r.hasItemOption=!1,r.initData(fi(e.data),[],function(e,t,n,i){if(e instanceof Array)return NaN;r.hasItemOption=!0;var a=e.value;if(a!=null)return a instanceof Array?a[i]:a}),r},defaultOption:{coordinateSystem:`globe`,globeIndex:0,geo3DIndex:0,zlevel:-10,polyline:!1,effect:{show:!1,period:4,trailWidth:4,trailLength:.2,spotIntensity:6},silent:!0,blendMode:`source-over`,lineStyle:{width:1,opacity:.5}}}),Bu=`@export ecgl.trail2.vertex
attribute vec3 position: POSITION;
attribute vec3 positionPrev;
attribute vec3 positionNext;
attribute float offset;
attribute float dist;
attribute float distAll;
attribute float start;

attribute vec4 a_Color : COLOR;

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;
uniform float near : NEAR;

uniform float speed : 0;
uniform float trailLength: 0.3;
uniform float time;
uniform float period: 1000;

uniform float spotSize: 1;

varying vec4 v_Color;
varying float v_Percent;
varying float v_SpotPercent;

@import ecgl.common.wireframe.vertexHeader

@import ecgl.lines3D.clipNear

void main()
{
 @import ecgl.lines3D.expandLine

 gl_Position = currProj;

 v_Color = a_Color;

 @import ecgl.common.wireframe.vertexMain

#ifdef CONSTANT_SPEED
 float t = mod((speed * time + start) / distAll, 1. + trailLength) - trailLength;
#else
 float t = mod((time + start) / period, 1. + trailLength) - trailLength;
#endif

 float trailLen = distAll * trailLength;

 v_Percent = (dist - t * distAll) / trailLen;

 v_SpotPercent = spotSize / distAll;

 }
@end


@export ecgl.trail2.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];
uniform float spotIntensity: 5;

varying vec4 v_Color;
varying float v_Percent;
varying float v_SpotPercent;

@import ecgl.common.wireframe.fragmentHeader

@import clay.util.srgb

void main()
{
 if (v_Percent > 1.0 || v_Percent < 0.0) {
 discard;
 }

 float fade = v_Percent;

#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color * v_Color);
#else
 gl_FragColor = color * v_Color;
#endif

 @import ecgl.common.wireframe.fragmentMain

 if (v_Percent > (1.0 - v_SpotPercent)) {
 gl_FragColor.rgb *= spotIntensity;
 }

 gl_FragColor.a *= fade;
}

@end`,Vu=Ea.vec3;function Hu(e){return e>0?1:-1}Q.Shader.import(Bu);var Uu=Q.Mesh.extend(function(){var e=new Q.Material({shader:new Q.Shader(Q.Shader.source(`ecgl.trail2.vertex`),Q.Shader.source(`ecgl.trail2.fragment`)),transparent:!0,depthMask:!1}),t=new ka({dynamic:!0});return t.createAttribute(`dist`,`float`,1),t.createAttribute(`distAll`,`float`,1),t.createAttribute(`start`,`float`,1),{geometry:t,material:e,culling:!1,$ignorePicking:!0}},{updateData:function(e,t,n){var r=e.hostModel,i=this.geometry,a=r.getModel(`effect`),o=a.get(`trailWidth`)*t.getDevicePixelRatio(),s=a.get(`trailLength`),c=r.get(`effect.constantSpeed`),l=r.get(`effect.period`)*1e3,u=c!=null;u?this.material.set(`speed`,c/1e3):this.material.set(`period`,l),this.material[u?`define`:`undefine`](`vertex`,`CONSTANT_SPEED`);var d=r.get(`polyline`);i.trailLength=s,this.material.set(`trailLength`,s),i.resetOffset(),[`position`,`positionPrev`,`positionNext`].forEach(function(e){i.attributes[e].value=n.attributes[e].value}),[`dist`,`distAll`,`start`,`offset`,`color`].forEach(function(e){i.attributes[e].init(i.vertexCount)}),i.indices=n.indices;var f=[],p=a.get(`trailColor`),m=a.get(`trailOpacity`),h=p!=null,g=m!=null;this.updateWorldTransform();var _=this.worldTransform.x.len(),v=this.worldTransform.y.len(),y=this.worldTransform.z.len(),b=0,x=0;e.each(function(t){var r=e.getItemLayout(t),a=g?m:lc(e,t),s=cc(e,t);a==null&&(a=1),f=Q.parseColor(h?p:s,f),f[3]*=a;for(var c=d?n.getPolylineVertexCount(r):n.getCubicCurveVertexCount(r[0],r[1],r[2],r[3]),S=0,C=[],w=[],T=b;T<b+c;T++)i.attributes.position.get(T,C),C[0]*=_,C[1]*=v,C[2]*=y,T>b&&(S+=Vu.dist(C,w)),i.attributes.dist.set(T,S),Vu.copy(w,C);x=Math.max(x,S);for(var E=Math.random()*(u?S:l),T=b;T<b+c;T++)i.attributes.distAll.set(T,S),i.attributes.start.set(T,E),i.attributes.offset.set(T,Hu(n.attributes.offset.get(T))*o/2),i.attributes.color.set(T,f);b+=c}),this.material.set(`spotSize`,x*.1*s),this.material.set(`spotIntensity`,a.get(`spotIntensity`)),i.dirty()},setAnimationTime:function(e){this.material.set(`time`,e)}});Q.Shader.import(Ka);function Wu(e){return e.radius==null?e.size==null?100:Math.max(e.size[0],e.size[1],e.size[2]):e.radius}var Gu=d.extend({type:`lines3D`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this._meshLinesMaterial=new Q.Material({shader:Q.createShader(`ecgl.meshLines3D`),transparent:!0,depthMask:!1}),this._linesMesh=new Q.Mesh({geometry:new ka,material:this._meshLinesMaterial,$ignorePicking:!0}),this._trailMesh=new Uu},render:function(e,t,n){this.groupGL.add(this._linesMesh);var r=e.coordinateSystem,i=e.getData();if(r&&r.viewGL){r.viewGL.add(this.groupGL),this._updateLines(e,t,n);var a=r.viewGL.isLinearSpace()?`define`:`undefine`;this._linesMesh.material[a](`fragment`,`SRGB_DECODE`),this._trailMesh.material[a](`fragment`,`SRGB_DECODE`)}var o=this._trailMesh;if(o.stopAnimation(),e.get(`effect.show`)){this.groupGL.add(o),o.updateData(i,n,this._linesMesh.geometry),o.__time=o.__time||0;var s=3600*1e3;this._curveEffectsAnimator=o.animate(``,{loop:!0}).when(s,{__time:s}).during(function(){o.setAnimationTime(o.__time)}).start()}else this.groupGL.remove(o),this._curveEffectsAnimator=null;this._linesMesh.material.blend=this._trailMesh.material.blend=e.get(`blendMode`)===`lighter`?Q.additiveBlend:null},pauseEffect:function(){this._curveEffectsAnimator&&this._curveEffectsAnimator.pause()},resumeEffect:function(){this._curveEffectsAnimator&&this._curveEffectsAnimator.resume()},toggleEffect:function(){var e=this._curveEffectsAnimator;e&&(e.isPaused()?e.resume():e.pause())},_updateLines:function(e,t,n){var r=e.getData(),i=e.coordinateSystem,a=this._linesMesh.geometry,o=e.get(`polyline`);a.expandLine=!0,a.segmentScale=Wu(i)/20;var s=`lineStyle.width`.split(`.`),c=n.getDevicePixelRatio(),l=0;r.each(function(e){var t=r.getItemModel(e).get(s);t==null&&(t=1),r.setItemVisual(e,`lineWidth`,t),l=Math.max(t,l)}),a.useNativeLine=!1;var u=0,d=0;r.each(function(e){var t=r.getItemLayout(e);o?(u+=a.getPolylineVertexCount(t),d+=a.getPolylineTriangleCount(t)):(u+=a.getCubicCurveVertexCount(t[0],t[1],t[2],t[3]),d+=a.getCubicCurveTriangleCount(t[0],t[1],t[2],t[3]))}),a.setVertexCount(u),a.setTriangleCount(d),a.resetOffset();var f=[];r.each(function(e){var t=r.getItemLayout(e),n=cc(r,e),i=lc(r,e),s=r.getItemVisual(e,`lineWidth`)*c;i==null&&(i=1),f=Q.parseColor(n,f),f[3]*=i,o?a.addPolyline(t,f,s):a.addCubicCurve(t[0],t[1],t[2],t[3],f,s)}),a.dirty()},remove:function(){this.groupGL.removeAll()},dispose:function(){this.groupGL.removeAll()}});function Ku(e){e.registerChartView(Gu),e.registerSeriesModel(zu),e.registerLayout(Ru),e.registerAction({type:`lines3DPauseEffect`,event:`lines3deffectpaused`,update:`series.lines3D:pauseEffect`},function(){}),e.registerAction({type:`lines3DResumeEffect`,event:`lines3deffectresumed`,update:`series.lines3D:resumeEffect`},function(){}),e.registerAction({type:`lines3DToggleEffect`,event:`lines3deffectchanged`,update:`series.lines3D:toggleEffect`},function(){})}h(Ku);function qu(e,t){for(var n=[],r=0;r<t.length;r++)n.push(e.dataToPoint(t[r]));return n}var Ju=u.extend({type:`series.polygons3D`,getRegionModel:function(e){return this.getData().getItemModel(e)},getRegionPolygonCoords:function(e){var t=this.coordinateSystem,n=this.getData().getItemModel(e),r=n.option instanceof Array?n.option:n.getShallow(`coords`);n.get(`multiPolygon`)||(r=[r]);for(var i=[],a=0;a<r.length;a++){for(var o=[],s=1;s<r[a].length;s++)o.push(qu(t,r[a][s]));i.push({exterior:qu(t,r[a][0]),interiors:o})}return i},getInitialData:function(e){var t=new n([`value`],this);return t.hasItemOption=!1,t.initData(fi(e.data),[],function(e,n,r,i){if(e instanceof Array)return NaN;t.hasItemOption=!0;var a=e.value;if(a!=null)return a instanceof Array?a[i]:a}),t},defaultOption:{show:!0,data:null,multiPolygon:!1,progressiveThreshold:1e3,progressive:1e3,zlevel:-10,label:{show:!1,distance:2,textStyle:{fontSize:20,color:`#000`,backgroundColor:`rgba(255,255,255,0.7)`,padding:3,borderRadius:4}},itemStyle:{color:`#fff`,borderWidth:0,borderColor:`#333`},emphasis:{itemStyle:{color:`#639fc0`},label:{show:!0}}}});m(Ju.prototype,vs);var Yu=d.extend({type:`polygons3D`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this._geo3DBuilderList=[],this._currentStep=0},render:function(e,t,n){this.groupGL.removeAll();var r=e.coordinateSystem;r&&r.viewGL&&r.viewGL.add(this.groupGL);var i=this._geo3DBuilderList[0];i||(i=new mc(n),i.extrudeY=r.type!==`mapbox3D`&&r.type!==`maptalks3D`,this._geo3DBuilderList[0]=i),this._updateShaderDefines(r,i),i.update(e,t,n),this._geo3DBuilderList.length=1,this.groupGL.add(i.rootNode)},incrementalPrepareRender:function(e,t,n){this.groupGL.removeAll();var r=e.coordinateSystem;r&&r.viewGL&&r.viewGL.add(this.groupGL),this._currentStep=0},incrementalRender:function(e,t,n,r){var i=this._geo3DBuilderList[this._currentStep],a=t.coordinateSystem;i||(i=new mc(r),i.extrudeY=a.type!==`mapbox3D`&&a.type!==`maptalks3D`,this._geo3DBuilderList[this._currentStep]=i),i.update(t,n,r,e.start,e.end),this.groupGL.add(i.rootNode),this._updateShaderDefines(a,i),this._currentStep++},_updateShaderDefines:function(e,t){var n=e.viewGL.isLinearSpace()?`define`:`undefine`;t.rootNode.traverse(function(t){t.material&&(t.material[n](`fragment`,`SRGB_DECODE`),(e.type===`mapbox3D`||e.type===`maptalks3D`)&&(t.material.define(`fragment`,`NORMAL_UP_AXIS`,2),t.material.define(`fragment`,`NORMAL_FRONT_AXIS`,1)))})},remove:function(){this.groupGL.removeAll()},dispose:function(){this.groupGL.removeAll(),this._geo3DBuilderList.forEach(function(e){e.dispose()})}});function Xu(e){e.registerChartView(Yu),e.registerSeriesModel(Ju)}h(Xu);var Zu=u.extend({type:`series.surface`,dependencies:[`globe`,`grid3D`,`geo3D`],visualStyleAccessPath:`itemStyle`,formatTooltip:function(e){return Wl(this,e)},getInitialData:function(e,t){var n=e.data;function r(e){return!(isNaN(e.min)||isNaN(e.max)||isNaN(e.step))}function i(e){var t=he;return Math.max(t(e.min),t(e.max),t(e.step))+1}if(!n)if(e.parametric){var a=e.parametricEquation||{},o=a.u||{},s=a.v||{};[`u`,`v`].forEach(function(e){r(a[e])}),[`x`,`y`,`z`].forEach(function(e){a[e]});var c=Math.floor((o.max+o.step-o.min)/o.step),l=Math.floor((s.max+s.step-s.min)/s.step);n=new Float32Array(c*l*5);for(var u=i(o),d=i(s),f=0,p=0;p<l;p++)for(var m=0;m<c;m++){var h=m*o.step+o.min,g=p*s.step+s.min,_=ve(Math.min(h,o.max),u),v=ve(Math.min(g,s.max),d),y=a.x(_,v),b=a.y(_,v),x=a.z(_,v);n[f++]=y,n[f++]=b,n[f++]=x,n[f++]=_,n[f++]=v}}else{var S=e.equation||{},C=S.x||{},w=S.y||{};if([`x`,`y`].forEach(function(e){r(S[e])}),typeof S.z!=`function`)return;var T=Math.floor((C.max+C.step-C.min)/C.step),E=Math.floor((w.max+w.step-w.min)/w.step);n=new Float32Array(T*E*3);for(var D=i(C),O=i(w),f=0,p=0;p<E;p++)for(var m=0;m<T;m++){var y=m*C.step+C.min,b=p*w.step+w.min,k=ve(Math.min(y,C.max),D),A=ve(Math.min(b,w.max),O),x=S.z(k,A);n[f++]=k,n[f++]=A,n[f++]=x}}var j=[`x`,`y`,`z`];return e.parametric&&j.push(`u`,`v`),Gl(this,j,n)},defaultOption:{coordinateSystem:`cartesian3D`,zlevel:-10,grid3DIndex:0,shading:`lambert`,parametric:!1,wireframe:{show:!0,lineStyle:{color:`rgba(0,0,0,0.5)`,width:1}},equation:{x:{min:-1,max:1,step:.1},y:{min:-1,max:1,step:.1},z:null},parametricEquation:{u:{min:-1,max:1,step:.1},v:{min:-1,max:1,step:.1},x:null,y:null,z:null},dataShape:null,itemStyle:{},animationDurationUpdate:500}});m(Zu.prototype,vs);var Qu=Ea.vec3;function $u(e){return isNaN(e[0])||isNaN(e[1])||isNaN(e[2])}var ed=d.extend({type:`surface`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node},render:function(e,t,n){var r=this._prevSurfaceMesh;this._prevSurfaceMesh=this._surfaceMesh,this._surfaceMesh=r,this._surfaceMesh||(this._surfaceMesh=this._createSurfaceMesh()),this.groupGL.remove(this._prevSurfaceMesh),this.groupGL.add(this._surfaceMesh);var i=e.coordinateSystem,a=e.get(`shading`),o=e.getData(),s=`ecgl.`+a;if((!this._surfaceMesh.material||this._surfaceMesh.material.shader.name!==s)&&(this._surfaceMesh.material=Q.createMaterial(s,[`VERTEX_COLOR`,`DOUBLE_SIDED`])),Q.setMaterialFromModel(a,this._surfaceMesh.material,e,n),i&&i.viewGL){i.viewGL.add(this.groupGL);var c=i.viewGL.isLinearSpace()?`define`:`undefine`;this._surfaceMesh.material[c](`fragment`,`SRGB_DECODE`)}var l=e.get(`parametric`),u=e.get(`dataShape`);u||(u=this._getDataShape(o,l));var d=e.getModel(`wireframe`),f=d.get(`lineStyle.width`),p=d.get(`show`)&&f>0;this._updateSurfaceMesh(this._surfaceMesh,e,u,p);var m=this._surfaceMesh.material;p?(m.define(`WIREFRAME_QUAD`),m.set(`wireframeLineWidth`,f),m.set(`wireframeLineColor`,Q.parseColor(d.get(`lineStyle.color`)))):m.undefine(`WIREFRAME_QUAD`),this._initHandler(e,n),this._updateAnimation(e)},_updateAnimation:function(e){Q.updateVertexAnimation([[`prevPosition`,`position`],[`prevNormal`,`normal`]],this._prevSurfaceMesh,this._surfaceMesh,e)},_createSurfaceMesh:function(){var e=new Q.Mesh({geometry:new Q.Geometry({dynamic:!0,sortTriangles:!0}),shadowDepthMaterial:new Q.Material({shader:new Q.Shader(Q.Shader.source(`ecgl.sm.depth.vertex`),Q.Shader.source(`ecgl.sm.depth.fragment`))}),culling:!1,renderOrder:10,renderNormal:!0});return e.geometry.createAttribute(`barycentric`,`float`,4),e.geometry.createAttribute(`prevPosition`,`float`,3),e.geometry.createAttribute(`prevNormal`,`float`,3),Object.assign(e.geometry,ac),e},_initHandler:function(e,t){var n=e.getData(),r=this._surfaceMesh,i=e.coordinateSystem;function a(e,t){for(var n=1/0,i=-1,a=[],o=0;o<e.length;o++){r.geometry.attributes.position.get(e[o],a);var s=Qu.dist(t.array,a);s<n&&(n=s,i=e[o])}return i}r.seriesIndex=e.seriesIndex;var o=-1;r.off(`mousemove`),r.off(`mouseout`),r.on(`mousemove`,function(e){var s=a(e.triangle,e.point);if(s>=0){var c=[];r.geometry.attributes.position.get(s,c);for(var l=i.pointToData(c),u=1/0,d=-1,f=[],p=0;p<n.count();p++){f[0]=n.get(`x`,p),f[1]=n.get(`y`,p),f[2]=n.get(`z`,p);var m=Qu.squaredDistance(f,l);m<u&&(d=p,u=m)}d!==o&&t.dispatchAction({type:`grid3DShowAxisPointer`,value:l}),o=d,r.dataIndex=d}else r.dataIndex=-1},this),r.on(`mouseout`,function(e){o=-1,r.dataIndex=-1,t.dispatchAction({type:`grid3DHideAxisPointer`})},this)},_updateSurfaceMesh:function(e,t,n,r){var i=e.geometry,a=t.getData(),o=a.getLayout(`points`),s=0;a.each(function(e){a.hasValue(e)||s++});var c=s||r,l=i.attributes.position,u=i.attributes.normal,d=i.attributes.texcoord0,f=i.attributes.barycentric,p=i.attributes.color,m=n[0],h=n[1],g=t.get(`shading`)!==`color`;if(c){var _=(m-1)*(h-1)*4;l.init(_),r&&f.init(_)}else l.value=new Float32Array(o);p.init(i.vertexCount),d.init(i.vertexCount);var v=[0,3,1,1,3,2],y=[[1,1,0,0],[0,1,0,1],[1,0,0,1],[1,0,1,0]],b=i.indices=new(i.vertexCount>65535?Uint32Array:Uint16Array)((m-1)*(h-1)*6),x=function(e,t,n){n[1]=e*h+t,n[0]=e*h+t+1,n[3]=(e+1)*h+t+1,n[2]=(e+1)*h+t},S=!1;if(c){var C=[],w=[],T=0;g?u.init(i.vertexCount):u.value=null;for(var E=[[],[],[]],D=[],O=[],k=Qu.create(),A=function(e,t,n){var r=t*3;return n[0]=e[r],n[1]=e[r+1],n[2]=e[r+2],n},j=new Float32Array(o.length),M=new Float32Array(o.length/3*4),N=0;N<a.count();N++)if(a.hasValue(N)){var ee=Q.parseColor(cc(a,N)),te=lc(a,N);te!=null&&(ee[3]*=te),ee[3]<.99&&(S=!0);for(var P=0;P<4;P++)M[N*4+P]=ee[P]}for(var ne=[1e7,1e7,1e7],N=0;N<m-1;N++)for(var re=0;re<h-1;re++){var ie=N*(h-1)+re,ae=ie*4;x(N,re,C);for(var F=!1,P=0;P<4;P++)A(o,C[P],w),$u(w)&&(F=!0);for(var P=0;P<4;P++)F?l.set(ae+P,ne):(A(o,C[P],w),l.set(ae+P,w)),r&&f.set(ae+P,y[P]);for(var P=0;P<6;P++)b[T++]=v[P]+ae;if(g&&!F)for(var P=0;P<2;P++){for(var oe=P*3,se=0;se<3;se++){var ce=C[v[oe]+se];A(o,ce,E[se])}Qu.sub(D,E[0],E[1]),Qu.sub(O,E[1],E[2]),Qu.cross(k,D,O);for(var se=0;se<3;se++){var le=C[v[oe]+se]*3;j[le]=j[le]+k[0],j[le+1]=j[le+1]+k[1],j[le+2]=j[le+2]+k[2]}}}if(g)for(var N=0;N<j.length/3;N++)A(j,N,k),Qu.normalize(k,k),j[N*3]=k[0],j[N*3+1]=k[1],j[N*3+2]=k[2];for(var ee=[],ue=[],N=0;N<m-1;N++)for(var re=0;re<h-1;re++){var ie=N*(h-1)+re,ae=ie*4;x(N,re,C);for(var P=0;P<4;P++){for(var se=0;se<4;se++)ee[se]=M[C[P]*4+se];p.set(ae+P,ee),g&&(A(j,C[P],k),u.set(ae+P,k));var ce=C[P];ue[0]=ce%h/(h-1),ue[1]=Math.floor(ce/h)/(m-1),d.set(ae+P,ue)}ie++}}else{for(var ue=[],N=0;N<a.count();N++){ue[0]=N%h/(h-1),ue[1]=Math.floor(N/h)/(m-1);var ee=Q.parseColor(cc(a,N)),te=lc(a,N);te!=null&&(ee[3]*=te),ee[3]<.99&&(S=!0),p.set(N,ee),d.set(N,ue)}for(var C=[],de=0,N=0;N<m-1;N++)for(var re=0;re<h-1;re++){x(N,re,C);for(var P=0;P<6;P++)b[de++]=C[v[P]]}g?i.generateVertexNormals():u.value=null}e.material.get(`normalMap`)&&i.generateTangents(),i.updateBoundingBox(),i.dirty(),e.material.transparent=S,e.material.depthMask=!S},_getDataShape:function(e,t){for(var n=-1/0,r=0,i=0,a=!1,o=t?`u`:`x`,s=e.count(),c=0;c<s;c++){var l=e.get(o,c);l<n&&(i=0,r++),n=l,i++}if((!r||i===1)&&(a=!0),!a)return[r+1,i];for(var u=Math.floor(Math.sqrt(s));u>0;){if(Math.floor(s/u)===s/u)return[u,s/u];u--}return u=Math.floor(Math.sqrt(s)),[u,u]},dispose:function(){this.groupGL.removeAll()},remove:function(){this.groupGL.removeAll()}});function td(e){e.registerChartView(ed),e.registerSeriesModel(Zu),e.registerLayout(function(e,t){e.eachSeriesByType(`surface`,function(e){var t=e.coordinateSystem;!t||t.type;var n=e.getData(),r=new Float32Array(3*n.count()),i=[NaN,NaN,NaN];if(t&&t.type===`cartesian3D`){var a=t.dimensions.map(function(t){return e.coordDimToDataDim(t)[0]});n.each(a,function(e,a,o,s){var c=n.hasValue(s)?t.dataToPoint([e,a,o]):i;r[s*3]=c[0],r[s*3+1]=c[1],r[s*3+2]=c[2]})}n.setLayout(`points`,r)})})}h(td);function nd(e,t){for(var n=[],r=0;r<t.length;r++)n.push(e.dataToPoint(t[r]));return n}var rd=u.extend({type:`series.map3D`,layoutMode:`box`,coordinateSystem:null,visualStyleAccessPath:`itemStyle`,optionUpdated:function(e){e=e||{};var t=this.get(`coordinateSystem`);t==null||t===`geo3D`||(this.get(`groundPlane.show`)&&(this.option.groundPlane.show=!1),this._geo=null)},getInitialData:function(e){e.data=this.getFilledRegions(e.data,e.map);var t=new n(Te(e.data,{coordDimensions:[`value`]}),this);t.initData(fi(e.data));var r={};return t.each(function(e){var n=t.getName(e);r[n]=t.getItemModel(e)}),this._regionModelMap=r,t},formatTooltip:function(e){return Wl(this,e)},getRegionModel:function(e){var t=this.getData().getName(e);return this._regionModelMap[t]||new _e(null,this)},getRegionPolygonCoords:function(e){var t=this.coordinateSystem,n=this.getData().getName(e);if(t.transform){var r=t.getRegion(n);return r?r.geometries:[]}else{this._geo||(this._geo=Cc.createGeo3D(this));for(var r=this._geo.getRegion(n),i=[],a=0;a<r.geometries.length;a++){var o=r.geometries[a],s=[],c=nd(t,o.exterior);if(s&&s.length)for(var l=0;l<o.interiors.length;l++)s.push(nd(t,s[l]));i.push({interiors:s,exterior:c})}return i}},getFormattedLabel:function(e,t){var n=Hl.getFormattedLabel(this,e,t);return n==null&&(n=this.getData().getName(e)),n},defaultOption:{coordinateSystem:`geo3D`,data:null}});m(rd.prototype,ys),m(rd.prototype,_a),m(rd.prototype,va),m(rd.prototype,ya),m(rd.prototype,vs);var id=d.extend({type:`map3D`,__ecgl__:!0,init:function(e,t){this._geo3DBuilder=new mc(t),this.groupGL=new Q.Node},render:function(e,t,n){var r=e.coordinateSystem;if(!(!r||!r.viewGL)){if(this.groupGL.add(this._geo3DBuilder.rootNode),r.viewGL.add(this.groupGL),r.type===`geo3D`){this._sceneHelper||(this._sceneHelper=new Ma,this._sceneHelper.initLight(this.groupGL)),this._sceneHelper.setScene(r.viewGL.scene),this._sceneHelper.updateLight(e),r.viewGL.setPostEffect(e.getModel(`postEffect`),n),r.viewGL.setTemporalSuperSampling(e.getModel(`temporalSuperSampling`));var i=this._control;i||(i=this._control=new wa({zr:n.getZr()}),this._control.init());var a=e.getModel(`viewControl`);i.setViewGL(r.viewGL),i.setFromViewControlModel(a,0),i.off(`update`),i.on(`update`,function(){n.dispatchAction({type:`map3DChangeCamera`,alpha:i.getAlpha(),beta:i.getBeta(),distance:i.getDistance(),from:this.uid,map3DId:e.id})}),this._geo3DBuilder.extrudeY=!0}else this._control&&(this._control.dispose(),this._control=null),this._sceneHelper&&(this._sceneHelper.dispose(),this._sceneHelper=null),e.getData().getLayout(`geo3D`),this._geo3DBuilder.extrudeY=!1;this._geo3DBuilder.update(e,t,n,0,e.getData().count());var o=r.viewGL.isLinearSpace()?`define`:`undefine`;this._geo3DBuilder.rootNode.traverse(function(e){e.material&&e.material[o](`fragment`,`SRGB_DECODE`)})}},afterRender:function(e,t,n,r){var i=r.renderer,a=e.coordinateSystem;a&&a.type===`geo3D`&&(this._sceneHelper.updateAmbientCubemap(i,e,n),this._sceneHelper.updateSkybox(i,e,n))},dispose:function(){this.groupGL.removeAll(),this._control.dispose(),this._geo3DBuilder.dispose()}});function ad(e){Tc(e),e.registerChartView(id),e.registerSeriesModel(rd),e.registerAction({type:`map3DChangeCamera`,event:`map3dcamerachanged`,update:`series:updateCamera`},function(e,t){t.eachComponent({mainType:`series`,subType:`map3D`,query:e},function(t){t.setView(e)})})}h(ad);var od=u.extend({type:`series.scatterGL`,dependencies:[`grid`,`polar`,`geo`,`singleAxis`],visualStyleAccessPath:`itemStyle`,hasSymbolVisual:!0,getInitialData:function(){return v(this)},defaultOption:{coordinateSystem:`cartesian2d`,zlevel:10,progressive:1e5,progressiveThreshold:1e5,large:!1,symbol:`circle`,symbolSize:10,zoomScale:0,blendMode:`source-over`,itemStyle:{opacity:.8},postEffect:{enable:!1,colorCorrection:{exposure:0,brightness:0,contrast:1,saturation:1,enable:!0}}}});function sd(e){this.viewGL=e}sd.prototype.reset=function(e,t){this._updateCamera(t.getWidth(),t.getHeight(),t.getDevicePixelRatio()),this._viewTransform=ye(),this.updateTransform(e,t)},sd.prototype.updateTransform=function(e,t){var n=e.coordinateSystem;n.getRoamTransform&&(we(this._viewTransform,n.getRoamTransform()),this._setCameraTransform(this._viewTransform),t.getZr().refresh())},sd.prototype.dataToPoint=function(e,t,n){n=e.dataToPoint(t,null,n);var r=this._viewTransform;r&&Ce(n,n,r)},sd.prototype.removeTransformInPoint=function(e){return this._viewTransform&&Ce(e,e,this._viewTransform),e},sd.prototype.getZoom=function(){if(this._viewTransform){var e=this._viewTransform;return 1/Math.max(Math.sqrt(e[0]*e[0]+e[1]*e[1]),Math.sqrt(e[2]*e[2]+e[3]*e[3]))}return 1},sd.prototype._setCameraTransform=function(e){var t=this.viewGL.camera;t.position.set(e[4],e[5],0),t.scale.set(Math.sqrt(e[0]*e[0]+e[1]*e[1]),Math.sqrt(e[2]*e[2]+e[3]*e[3]),1)},sd.prototype._updateCamera=function(e,t,n){this.viewGL.setViewport(0,0,e,t,n);var r=this.viewGL.camera;r.left=r.top=0,r.bottom=t,r.right=e,r.near=0,r.far=100};var cd=d.extend({type:`scatterGL`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this.viewGL=new ns(`orthographic`),this.viewGL.add(this.groupGL),this._pointsBuilderList=[],this._currentStep=0,this._sizeScale=1,this._glViewHelper=new sd(this.viewGL)},render:function(e,t,n){if(this.groupGL.removeAll(),this._glViewHelper.reset(e,n),e.getData().count()){var r=this._pointsBuilderList[0];r||(r=this._pointsBuilderList[0]=new gu(!0,n)),this._pointsBuilderList.length=1,this.groupGL.add(r.rootNode),this._removeTransformInPoints(e.getData().getLayout(`points`)),r.update(e,t,n),this.viewGL.setPostEffect(e.getModel(`postEffect`),n)}},incrementalPrepareRender:function(e,t,n){this.groupGL.removeAll(),this._glViewHelper.reset(e,n),this._currentStep=0,this.viewGL.setPostEffect(e.getModel(`postEffect`),n)},incrementalRender:function(e,t,n,r){if(!(e.end<=e.start)){var i=this._pointsBuilderList[this._currentStep];i||(i=new gu(!0,r),this._pointsBuilderList[this._currentStep]=i),this.groupGL.add(i.rootNode),this._removeTransformInPoints(t.getData().getLayout(`points`)),i.setSizeScale(this._sizeScale),i.update(t,n,r,e.start,e.end),r.getZr().refresh(),this._currentStep++}},updateTransform:function(e,t,n){if(e.coordinateSystem.getRoamTransform){this._glViewHelper.updateTransform(e,n);var r=this._glViewHelper.getZoom(),i=Math.max((e.get(`zoomScale`)||0)*(r-1)+1,0);this._sizeScale=i,this._pointsBuilderList.forEach(function(e){e.setSizeScale(i)})}},_removeTransformInPoints:function(e){if(e)for(var t=[],n=0;n<e.length;n+=2)t[0]=e[n],t[1]=e[n+1],this._glViewHelper.removeTransformInPoint(t),e[n]=t[0],e[n+1]=t[1]},dispose:function(){this.groupGL.removeAll(),this._pointsBuilderList.forEach(function(e){e.dispose()})},remove:function(){this.groupGL.removeAll()}});function ld(e){e.registerChartView(cd),e.registerSeriesModel(od),e.registerLayout({seriesType:`scatterGL`,reset:function(e){var t=e.coordinateSystem,n=e.getData(),r;if(t){var i=t.dimensions.map(function(e){return n.mapDimension(e)}).slice(0,2),a=[];i.length===1?r=function(e){for(var r=new Float32Array((e.end-e.start)*2),a=e.start;a<e.end;a++){var o=(a-e.start)*2,s=n.get(i[0],a),c=t.dataToPoint(s);r[o]=c[0],r[o+1]=c[1]}n.setLayout(`points`,r)}:i.length===2&&(r=function(e){for(var r=new Float32Array((e.end-e.start)*2),o=e.start;o<e.end;o++){var s=(o-e.start)*2,c=n.get(i[0],o),l=n.get(i[1],o);a[0]=c,a[1]=l,a=t.dataToPoint(a),r[s]=a[0],r[s+1]=a[1]}n.setLayout(`points`,r)})}return{progress:r}}})}h(ld);function ud(e,t,r,i,a){for(var o=new Se(i),s=0;s<e.length;s++)o.addNode(X.firstNotNull(e[s].id,e[s].name,s),s);for(var c=[],l=[],u=0,s=0;s<t.length;s++){var d=t[s],f=d.source,p=d.target;o.addEdge(f,p,u)&&(l.push(d),c.push(X.firstNotNull(d.id,f+` > `+p)),u++)}var m=new n(Te(e,{coordDimensions:[`value`]}),r);m.initData(e);var h=new n([`value`],r);return h.initData(l,c),a&&a(m,h),ge({mainData:m,struct:o,structAttr:`graph`,datas:{node:m,edge:h},datasAttr:{node:`data`,edge:`edgeData`}}),o.update(),o}var dd=u.extend({type:`series.graphGL`,visualStyleAccessPath:`itemStyle`,hasSymbolVisual:!0,init:function(e){dd.superApply(this,`init`,arguments),this.legendDataProvider=function(){return this._categoriesData},this._updateCategoriesData()},mergeOption:function(e){dd.superApply(this,`mergeOption`,arguments),this._updateCategoriesData()},getFormattedLabel:function(e,t,n,r){var i=Hl.getFormattedLabel(this,e,t,n,r);if(i==null){var a=this.getData(),o=a.dimensions[a.dimensions.length-1];i=a.get(o,e)}return i},getInitialData:function(e,t){var n=e.edges||e.links||[],r=e.data||e.nodes||[],i=this;if(r&&n)return ud(r,n,this,!0,a).data;function a(e,n){e.wrapMethod(`getItemModel`,function(e){let t=i._categoriesModels[e.getShallow(`category`)];return t&&(t.parentModel=e.parentModel,e.parentModel=t),e});let r=t.getModel([]).getModel;function a(e,t){let n=r.call(this,e,t);return n.resolveParentPath=o,n}n.wrapMethod(`getItemModel`,function(e){return e.resolveParentPath=o,e.getModel=a,e});function o(e){if(e&&(e[0]===`label`||e[1]===`label`)){let t=e.slice();return e[0]===`label`?t[0]=`edgeLabel`:e[1]===`label`&&(t[1]=`edgeLabel`),t}return e}}},getGraph:function(){return this.getData().graph},getEdgeData:function(){return this.getGraph().edgeData},getCategoriesData:function(){return this._categoriesData},formatTooltip:function(e,t,n){if(n===`edge`){var r=this.getData(),i=this.getDataParams(e,n),a=r.graph.getEdgeByIndex(e),o=r.getName(a.node1.dataIndex),s=r.getName(a.node2.dataIndex),c=[];return o!=null&&c.push(o),s!=null&&c.push(s),c=j(c.join(` > `)),i.value&&(c+=` : `+j(i.value)),c}else return dd.superApply(this,`formatTooltip`,arguments)},_updateCategoriesData:function(){var e=(this.option.categories||[]).map(function(e){return e.value==null?Object.assign({value:0},e):e}),t=new n([`value`],this);t.initData(e),this._categoriesData=t,this._categoriesModels=t.mapArray(function(e){return t.getItemModel(e,!0)})},setView:function(e){e.zoom!=null&&(this.option.zoom=e.zoom),e.offset!=null&&(this.option.offset=e.offset)},setNodePosition:function(e){for(var t=0;t<e.length/2;t++){var n=e[t*2],r=e[t*2+1],i=this.getData().getRawDataItem(t);i.x=n,i.y=r}},isAnimationEnabled:function(){return dd.superCall(this,`isAnimationEnabled`)&&!(this.get(`layout`)===`force`&&this.get(`force.layoutAnimation`))},defaultOption:{zlevel:10,z:2,legendHoverLink:!0,layout:`forceAtlas2`,forceAtlas2:{initLayout:null,GPU:!0,steps:1,maxSteps:1e3,repulsionByDegree:!0,linLogMode:!1,strongGravityMode:!1,gravity:1,edgeWeightInfluence:1,edgeWeight:[1,4],nodeWeight:[1,4],preventOverlap:!1,gravityCenter:null},focusNodeAdjacency:!0,focusNodeAdjacencyOn:`mouseover`,left:`center`,top:`center`,symbol:`circle`,symbolSize:5,roam:!1,center:null,zoom:1,label:{show:!1,formatter:`{b}`,position:`right`,distance:5,textStyle:{fontSize:14}},itemStyle:{},lineStyle:{color:`#aaa`,width:1,opacity:.5},emphasis:{label:{show:!0}},animation:!1}}),fd=Ea.vec2,pd=[[0,0],[1,1]],md=Y.extend(function(){return{segmentScale:4,dynamic:!0,useNativeLine:!0,attributes:{position:new Y.Attribute(`position`,`float`,2,`POSITION`),normal:new Y.Attribute(`normal`,`float`,2),offset:new Y.Attribute(`offset`,`float`,1),color:new Y.Attribute(`color`,`float`,4,`COLOR`)}}},{resetOffset:function(){this._vertexOffset=0,this._faceOffset=0,this._itemVertexOffsets=[]},setVertexCount:function(e){var t=this.attributes;this.vertexCount!==e&&(t.position.init(e),t.color.init(e),this.useNativeLine||(t.offset.init(e),t.normal.init(e)),e>65535?this.indices instanceof Uint16Array&&(this.indices=new Uint32Array(this.indices)):this.indices instanceof Uint32Array&&(this.indices=new Uint16Array(this.indices)))},setTriangleCount:function(e){this.triangleCount!==e&&(e===0?this.indices=null:this.indices=this.vertexCount>65535?new Uint32Array(e*3):new Uint16Array(e*3))},_getCubicCurveApproxStep:function(e,t,n,r){return 1/(fd.dist(e,t)+fd.dist(n,t)+fd.dist(r,n)+1)*this.segmentScale},getCubicCurveVertexCount:function(e,t,n,r){var i=this._getCubicCurveApproxStep(e,t,n,r),a=Math.ceil(1/i);return this.useNativeLine?a*2:a*2+2},getCubicCurveTriangleCount:function(e,t,n,r){var i=this._getCubicCurveApproxStep(e,t,n,r),a=Math.ceil(1/i);return this.useNativeLine?0:a*2},getLineVertexCount:function(){return this.getPolylineVertexCount(pd)},getLineTriangleCount:function(){return this.getPolylineTriangleCount(pd)},getPolylineVertexCount:function(e){var t=typeof e==`number`?e:typeof e[0]==`number`?e.length/2:e.length;return this.useNativeLine?(t-1)*2:(t-1)*2+2},getPolylineTriangleCount:function(e){var t=typeof e==`number`?e:typeof e[0]==`number`?e.length/2:e.length;return this.useNativeLine?0:(t-1)*2},addCubicCurve:function(e,t,n,r,i,a){a==null&&(a=1);for(var o=e[0],s=e[1],c=t[0],l=t[1],u=n[0],d=n[1],f=r[0],p=r[1],m=this._getCubicCurveApproxStep(e,t,n,r),h=m*m,g=h*m,_=3*m,v=3*h,y=6*h,b=6*g,x=o-c*2+u,S=s-l*2+d,C=(c-u)*3-o+f,w=(l-d)*3-s+p,T=o,E=s,D=(c-o)*_+x*v+C*g,O=(l-s)*_+S*v+w*g,k=x*y+C*b,A=S*y+w*b,j=C*b,M=w*b,N=0,ee=0,te=Math.ceil(1/m),P=new Float32Array((te+1)*3),P=[],ne=0,ee=0;ee<te+1;ee++)P[ne++]=T,P[ne++]=E,T+=D,E+=O,D+=k,O+=A,k+=j,A+=M,N+=m,N>1&&(T=D>0?Math.min(T,f):Math.max(T,f),E=O>0?Math.min(E,p):Math.max(E,p));this.addPolyline(P,i,a)},addLine:function(e,t,n,r){this.addPolyline([e,t],n,r)},addPolyline:function(){var e=fd.create(),t=fd.create(),n=fd.create(),r=fd.create(),i=[],a=[],o=[];return function(s,c,l,u,d){if(s.length){var f=typeof s[0]!=`number`;if(d==null&&(d=f?s.length:s.length/2),!(d<2)){u==null&&(u=0),l==null&&(l=1),this._itemVertexOffsets.push(this._vertexOffset);for(var p=f?typeof c[0]!=`number`:c.length/4===d,m=this.attributes.position,h=this.attributes.color,g=this.attributes.offset,_=this.attributes.normal,v=this.indices,y=this._vertexOffset,b,x=0;x<d;x++){if(f)i=s[x+u],b=p?c[x+u]:c;else{var S=x*2+u;if(i=i||[],i[0]=s[S],i[1]=s[S+1],p){var C=x*4+u;b=b||[],b[0]=c[C],b[1]=c[C+1],b[2]=c[C+2],b[3]=c[C+3]}else b=c}if(this.useNativeLine)x>1&&(m.copy(y,y-1),h.copy(y,y-1),y++);else{var w;if(x<d-1){if(f)fd.copy(a,s[x+1]);else{var S=(x+1)*2+u;a=a||[],a[0]=s[S],a[1]=s[S+1]}if(x>0){fd.sub(e,i,o),fd.sub(t,a,i),fd.normalize(e,e),fd.normalize(t,t),fd.add(r,e,t),fd.normalize(r,r);var T=l/2*Math.min(1/fd.dot(e,r),2);n[0]=-r[1],n[1]=r[0],w=T}else fd.sub(e,a,i),fd.normalize(e,e),n[0]=-e[1],n[1]=e[0],w=l/2}else fd.sub(e,i,o),fd.normalize(e,e),n[0]=-e[1],n[1]=e[0],w=l/2;_.set(y,n),_.set(y+1,n),g.set(y,w),g.set(y+1,-w),fd.copy(o,i),m.set(y,i),m.set(y+1,i),h.set(y,b),h.set(y+1,b),y+=2}if(this.useNativeLine)h.set(y,b),m.set(y,i),y++;else if(x>0){var E=this._faceOffset*3,v=this.indices;v[E]=y-4,v[E+1]=y-3,v[E+2]=y-2,v[E+3]=y-3,v[E+4]=y-1,v[E+5]=y-2,this._faceOffset+=2}}this._vertexOffset=y}}}}(),setItemColor:function(e,t){for(var n=this._itemVertexOffsets[e],r=e<this._itemVertexOffsets.length-1?this._itemVertexOffsets[e+1]:this._vertexOffset,i=n;i<r;i++)this.attributes.color.set(i,t);this.dirty(`color`)}});C(md.prototype,Ta),Q.Shader.import(`@export ecgl.forceAtlas2.updateNodeRepulsion

#define NODE_COUNT 0

uniform sampler2D positionTex;

uniform vec2 textureSize;
uniform float gravity;
uniform float scaling;
uniform vec2 gravityCenter;

uniform bool strongGravityMode;
uniform bool preventOverlap;

varying vec2 v_Texcoord;

void main() {

 vec4 n0 = texture2D(positionTex, v_Texcoord);

 vec2 force = vec2(0.0);
 for (int i = 0; i < NODE_COUNT; i++) {
 vec2 uv = vec2(
 mod(float(i), textureSize.x) / (textureSize.x - 1.0),
 floor(float(i) / textureSize.x) / (textureSize.y - 1.0)
 );
 vec4 n1 = texture2D(positionTex, uv);

 vec2 dir = n0.xy - n1.xy;
 float d2 = dot(dir, dir);

 if (d2 > 0.0) {
 float factor = 0.0;
 if (preventOverlap) {
 float d = sqrt(d2);
 d = d - n0.w - n1.w;
 if (d > 0.0) {
 factor = scaling * n0.z * n1.z / (d * d);
 }
 else if (d < 0.0) {
 factor = scaling * 100.0 * n0.z * n1.z;
 }
 }
 else {
 factor = scaling * n0.z * n1.z / d2;
 }
 force += dir * factor;
 }
 }

 vec2 dir = gravityCenter - n0.xy;
 float d = 1.0;
 if (!strongGravityMode) {
 d = length(dir);
 }

 force += dir * n0.z * gravity / (d + 1.0);

 gl_FragColor = vec4(force, 0.0, 1.0);
}
@end

@export ecgl.forceAtlas2.updateEdgeAttraction.vertex

attribute vec2 node1;
attribute vec2 node2;
attribute float weight;

uniform sampler2D positionTex;
uniform float edgeWeightInfluence;
uniform bool preventOverlap;
uniform bool linLogMode;

uniform vec2 windowSize: WINDOW_SIZE;

varying vec2 v_Force;

void main() {

 vec4 n0 = texture2D(positionTex, node1);
 vec4 n1 = texture2D(positionTex, node2);

 vec2 dir = n1.xy - n0.xy;
 float d = length(dir);
 float w;
 if (edgeWeightInfluence == 0.0) {
 w = 1.0;
 }
 else if (edgeWeightInfluence == 1.0) {
 w = weight;
 }
 else {
 w = pow(weight, edgeWeightInfluence);
 }
 vec2 offset = vec2(1.0 / windowSize.x, 1.0 / windowSize.y);
 vec2 scale = vec2((windowSize.x - 1.0) / windowSize.x, (windowSize.y - 1.0) / windowSize.y);
 vec2 pos = node1 * scale * 2.0 - 1.0;
 gl_Position = vec4(pos + offset, 0.0, 1.0);
 gl_PointSize = 1.0;

 float factor;
 if (preventOverlap) {
 d = d - n1.w - n0.w;
 }
 if (d <= 0.0) {
 v_Force = vec2(0.0);
 return;
 }

 if (linLogMode) {
 factor = w * log(d) / d;
 }
 else {
 factor = w;
 }
 v_Force = dir * factor;
}
@end

@export ecgl.forceAtlas2.updateEdgeAttraction.fragment

varying vec2 v_Force;

void main() {
 gl_FragColor = vec4(v_Force, 0.0, 0.0);
}
@end

@export ecgl.forceAtlas2.calcWeightedSum.vertex

attribute vec2 node;

varying vec2 v_NodeUv;

void main() {

 v_NodeUv = node;
 gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
 gl_PointSize = 1.0;
}
@end

@export ecgl.forceAtlas2.calcWeightedSum.fragment

varying vec2 v_NodeUv;

uniform sampler2D positionTex;
uniform sampler2D forceTex;
uniform sampler2D forcePrevTex;

void main() {
 vec2 force = texture2D(forceTex, v_NodeUv).rg;
 vec2 forcePrev = texture2D(forcePrevTex, v_NodeUv).rg;

 float mass = texture2D(positionTex, v_NodeUv).z;
 float swing = length(force - forcePrev) * mass;
 float traction = length(force + forcePrev) * 0.5 * mass;

 gl_FragColor = vec4(swing, traction, 0.0, 0.0);
}
@end

@export ecgl.forceAtlas2.calcGlobalSpeed

uniform sampler2D globalSpeedPrevTex;
uniform sampler2D weightedSumTex;
uniform float jitterTolerence;

void main() {
 vec2 weightedSum = texture2D(weightedSumTex, vec2(0.5)).xy;
 float prevGlobalSpeed = texture2D(globalSpeedPrevTex, vec2(0.5)).x;
 float globalSpeed = jitterTolerence * jitterTolerence
 * weightedSum.y / weightedSum.x;
 if (prevGlobalSpeed > 0.0) {
 globalSpeed = min(globalSpeed / prevGlobalSpeed, 1.5) * prevGlobalSpeed;
 }
 gl_FragColor = vec4(globalSpeed, 0.0, 0.0, 1.0);
}
@end

@export ecgl.forceAtlas2.updatePosition

uniform sampler2D forceTex;
uniform sampler2D forcePrevTex;
uniform sampler2D positionTex;
uniform sampler2D globalSpeedTex;

varying vec2 v_Texcoord;

void main() {
 vec2 force = texture2D(forceTex, v_Texcoord).xy;
 vec2 forcePrev = texture2D(forcePrevTex, v_Texcoord).xy;
 vec4 node = texture2D(positionTex, v_Texcoord);

 float globalSpeed = texture2D(globalSpeedTex, vec2(0.5)).r;
 float swing = length(force - forcePrev);
 float speed = 0.1 * globalSpeed / (0.1 + globalSpeed * sqrt(swing));

 float df = length(force);
 if (df > 0.0) {
 speed = min(df * speed, 10.0) / df;

 gl_FragColor = vec4(node.xy + speed * force, node.zw);
 }
 else {
 gl_FragColor = node;
 }
}
@end

@export ecgl.forceAtlas2.edges.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

attribute vec2 node;
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;

uniform sampler2D positionTex;

void main()
{
 gl_Position = worldViewProjection * vec4(
 texture2D(positionTex, node).xy, -10.0, 1.0
 );
 v_Color = a_Color;
}
@end

@export ecgl.forceAtlas2.edges.fragment
uniform vec4 color : [1.0, 1.0, 1.0, 1.0];
varying vec4 v_Color;
void main() {
 gl_FragColor = color * v_Color;
}
@end`);var hd={repulsionByDegree:!0,linLogMode:!1,strongGravityMode:!1,gravity:1,scaling:1,edgeWeightInfluence:1,jitterTolerence:.1,preventOverlap:!1,dissuadeHubs:!1,gravityCenter:null};function gd(e){var t={type:Q.Texture.FLOAT,minFilter:Q.Texture.NEAREST,magFilter:Q.Texture.NEAREST};this._positionSourceTex=new Q.Texture2D(t),this._positionSourceTex.flipY=!1,this._positionTex=new Q.Texture2D(t),this._positionPrevTex=new Q.Texture2D(t),this._forceTex=new Q.Texture2D(t),this._forcePrevTex=new Q.Texture2D(t),this._weightedSumTex=new Q.Texture2D(t),this._weightedSumTex.width=this._weightedSumTex.height=1,this._globalSpeedTex=new Q.Texture2D(t),this._globalSpeedPrevTex=new Q.Texture2D(t),this._globalSpeedTex.width=this._globalSpeedTex.height=1,this._globalSpeedPrevTex.width=this._globalSpeedPrevTex.height=1,this._nodeRepulsionPass=new bi({fragment:Q.Shader.source(`ecgl.forceAtlas2.updateNodeRepulsion`)}),this._positionPass=new bi({fragment:Q.Shader.source(`ecgl.forceAtlas2.updatePosition`)}),this._globalSpeedPass=new bi({fragment:Q.Shader.source(`ecgl.forceAtlas2.calcGlobalSpeed`)}),this._copyPass=new bi({fragment:Q.Shader.source(`clay.compositor.output`)});var n=function(e){e.blendEquation(e.FUNC_ADD),e.blendFunc(e.ONE,e.ONE)};this._edgeForceMesh=new Q.Mesh({geometry:new Q.Geometry({attributes:{node1:new Q.Geometry.Attribute(`node1`,`float`,2),node2:new Q.Geometry.Attribute(`node2`,`float`,2),weight:new Q.Geometry.Attribute(`weight`,`float`,1)},dynamic:!0,mainAttribute:`node1`}),material:new Q.Material({transparent:!0,shader:Q.createShader(`ecgl.forceAtlas2.updateEdgeAttraction`),blend:n,depthMask:!1,depthText:!1}),mode:Q.Mesh.POINTS}),this._weightedSumMesh=new Q.Mesh({geometry:new Q.Geometry({attributes:{node:new Q.Geometry.Attribute(`node`,`float`,2)},dynamic:!0,mainAttribute:`node`}),material:new Q.Material({transparent:!0,shader:Q.createShader(`ecgl.forceAtlas2.calcWeightedSum`),blend:n,depthMask:!1,depthText:!1}),mode:Q.Mesh.POINTS}),this._framebuffer=new Or({depthBuffer:!1}),this._dummyCamera=new Q.OrthographicCamera({left:-1,right:1,top:1,bottom:-1,near:0,far:100}),this._globalSpeed=0}gd.prototype.updateOption=function(e){for(var t in hd)this[t]=hd[t];var n=this._nodes.length;if(n>5e4?this.jitterTolerence=10:n>5e3?this.jitterTolerence=1:this.jitterTolerence=.1,n>100?this.scaling=2:this.scaling=10,e)for(var t in hd)e[t]!=null&&(this[t]=e[t]);if(this.repulsionByDegree)for(var r=this._positionSourceTex.pixels,i=0;i<this._nodes.length;i++)r[i*4+2]=(this._nodes[i].degree||0)+1},gd.prototype._updateGravityCenter=function(e){var t=this._nodes,n=this._edges;if(this.gravityCenter)this._gravityCenter=this.gravityCenter;else{for(var r=[1/0,1/0],i=[-1/0,-1/0],a=0;a<t.length;a++)r[0]=Math.min(t[a].x,r[0]),r[1]=Math.min(t[a].y,r[1]),i[0]=Math.max(t[a].x,i[0]),i[1]=Math.max(t[a].y,i[1]);this._gravityCenter=[(r[0]+i[0])*.5,(r[1]+i[1])*.5]}for(var a=0;a<n.length;a++){var o=n[a].node1,s=n[a].node2;t[o].degree=(t[o].degree||0)+1,t[s].degree=(t[s].degree||0)+1}},gd.prototype.initData=function(e,t){this._nodes=e,this._edges=t,this._updateGravityCenter();var n=Math.ceil(Math.sqrt(e.length)),r=n,i=new Float32Array(n*r*4);this._resize(n,r);for(var a=0,o=0;o<e.length;o++){var s=e[o];i[a++]=s.x||0,i[a++]=s.y||0,i[a++]=s.mass||1,i[a++]=s.size||1}this._positionSourceTex.pixels=i;var c=this._edgeForceMesh.geometry,l=t.length;c.attributes.node1.init(l*2),c.attributes.node2.init(l*2),c.attributes.weight.init(l*2);for(var u=[],o=0;o<t.length;o++){var d=c.attributes,f=t[o].weight;f==null&&(f=1),d.node1.set(o,this.getNodeUV(t[o].node1,u)),d.node2.set(o,this.getNodeUV(t[o].node2,u)),d.weight.set(o,f),d.node1.set(o+l,this.getNodeUV(t[o].node2,u)),d.node2.set(o+l,this.getNodeUV(t[o].node1,u)),d.weight.set(o+l,f)}var p=this._weightedSumMesh.geometry;p.attributes.node.init(e.length);for(var o=0;o<e.length;o++)p.attributes.node.set(o,this.getNodeUV(o,u));c.dirty(),p.dirty(),this._nodeRepulsionPass.material.define(`fragment`,`NODE_COUNT`,e.length),this._nodeRepulsionPass.material.setUniform(`textureSize`,[n,r]),this._inited=!1,this._frame=0},gd.prototype.getNodes=function(){return this._nodes},gd.prototype.getEdges=function(){return this._edges},gd.prototype.step=function(e){this._inited||(this._initFromSource(e),this._inited=!0),this._frame++,this._framebuffer.attach(this._forceTex),this._framebuffer.bind(e);var t=this._nodeRepulsionPass;t.setUniform(`strongGravityMode`,this.strongGravityMode),t.setUniform(`gravity`,this.gravity),t.setUniform(`gravityCenter`,this._gravityCenter),t.setUniform(`scaling`,this.scaling),t.setUniform(`preventOverlap`,this.preventOverlap),t.setUniform(`positionTex`,this._positionPrevTex),t.render(e);var n=this._edgeForceMesh;n.material.set(`linLogMode`,this.linLogMode),n.material.set(`edgeWeightInfluence`,this.edgeWeightInfluence),n.material.set(`preventOverlap`,this.preventOverlap),n.material.set(`positionTex`,this._positionPrevTex),e.gl.enable(e.gl.BLEND),e.renderPass([n],this._dummyCamera),this._framebuffer.attach(this._weightedSumTex),e.gl.clearColor(0,0,0,0),e.gl.clear(e.gl.COLOR_BUFFER_BIT),e.gl.enable(e.gl.BLEND);var r=this._weightedSumMesh;r.material.set(`positionTex`,this._positionPrevTex),r.material.set(`forceTex`,this._forceTex),r.material.set(`forcePrevTex`,this._forcePrevTex),e.renderPass([r],this._dummyCamera),this._framebuffer.attach(this._globalSpeedTex);var i=this._globalSpeedPass;i.setUniform(`globalSpeedPrevTex`,this._globalSpeedPrevTex),i.setUniform(`weightedSumTex`,this._weightedSumTex),i.setUniform(`jitterTolerence`,this.jitterTolerence),e.gl.disable(e.gl.BLEND),i.render(e);var a=this._positionPass;this._framebuffer.attach(this._positionTex),a.setUniform(`globalSpeedTex`,this._globalSpeedTex),a.setUniform(`positionTex`,this._positionPrevTex),a.setUniform(`forceTex`,this._forceTex),a.setUniform(`forcePrevTex`,this._forcePrevTex),a.render(e),this._framebuffer.unbind(e),this._swapTexture()},gd.prototype.update=function(e,t,n){t==null&&(t=1),t=Math.max(t,1);for(var r=0;r<t;r++)this.step(e);n&&n()},gd.prototype.getNodePositionTexture=function(){return this._inited?this._positionPrevTex:this._positionSourceTex},gd.prototype.getNodeUV=function(e,t){t=t||[];var n=this._positionTex.width,r=this._positionTex.height;return t[0]=e%n/(n-1),t[1]=Math.floor(e/n)/(r-1)||0,t},gd.prototype.getNodePosition=function(e,t){var n=this._positionArr,r=this._positionTex.width,i=this._positionTex.height,a=r*i;(!n||n.length!==a*4)&&(n=this._positionArr=new Float32Array(a*4)),this._framebuffer.bind(e),this._framebuffer.attach(this._positionPrevTex),e.gl.readPixels(0,0,r,i,e.gl.RGBA,e.gl.FLOAT,n),this._framebuffer.unbind(e),t||(t=new Float32Array(this._nodes.length*2));for(var o=0;o<this._nodes.length;o++)t[o*2]=n[o*4],t[o*2+1]=n[o*4+1];return t},gd.prototype.getTextureData=function(e,t){var n=this[`_`+t+`Tex`],r=n.width,i=n.height;this._framebuffer.bind(e),this._framebuffer.attach(n);var a=new Float32Array(r*i*4);return e.gl.readPixels(0,0,r,i,e.gl.RGBA,e.gl.FLOAT,a),this._framebuffer.unbind(e),a},gd.prototype.getTextureSize=function(){return{width:this._positionTex.width,height:this._positionTex.height}},gd.prototype.isFinished=function(e){return this._frame>e},gd.prototype._swapTexture=function(){var e=this._positionPrevTex;this._positionPrevTex=this._positionTex,this._positionTex=e;var e=this._forcePrevTex;this._forcePrevTex=this._forceTex,this._forceTex=e;var e=this._globalSpeedPrevTex;this._globalSpeedPrevTex=this._globalSpeedTex,this._globalSpeedTex=e},gd.prototype._initFromSource=function(e){this._framebuffer.attach(this._positionPrevTex),this._framebuffer.bind(e),this._copyPass.setUniform(`texture`,this._positionSourceTex),this._copyPass.render(e),e.gl.clearColor(0,0,0,0),this._framebuffer.attach(this._forcePrevTex),e.gl.clear(e.gl.COLOR_BUFFER_BIT),this._framebuffer.attach(this._globalSpeedPrevTex),e.gl.clear(e.gl.COLOR_BUFFER_BIT),this._framebuffer.unbind(e)},gd.prototype._resize=function(e,t){[`_positionSourceTex`,`_positionTex`,`_positionPrevTex`,`_forceTex`,`_forcePrevTex`].forEach(function(n){this[n].width=e,this[n].height=t,this[n].dirty()},this)},gd.prototype.dispose=function(e){this._framebuffer.dispose(e),this._copyPass.dispose(e),this._nodeRepulsionPass.dispose(e),this._positionPass.dispose(e),this._globalSpeedPass.dispose(e),this._edgeForceMesh.geometry.dispose(e),this._weightedSumMesh.geometry.dispose(e),this._positionSourceTex.dispose(e),this._positionTex.dispose(e),this._positionPrevTex.dispose(e),this._forceTex.dispose(e),this._forcePrevTex.dispose(e),this._weightedSumTex.dispose(e),this._globalSpeedTex.dispose(e),this._globalSpeedPrevTex.dispose(e)};function _d(){var e={create:function(){return new Float32Array(2)},dist:function(e,t){var n=t[0]-e[0],r=t[1]-e[1];return Math.sqrt(n*n+r*r)},len:function(e){var t=e[0],n=e[1];return Math.sqrt(t*t+n*n)},scaleAndAdd:function(e,t,n,r){return e[0]=t[0]+n[0]*r,e[1]=t[1]+n[1]*r,e},scale:function(e,t,n){return e[0]=t[0]*n,e[1]=t[1]*n,e},add:function(e,t,n){return e[0]=t[0]+n[0],e[1]=t[1]+n[1],e},sub:function(e,t,n){return e[0]=t[0]-n[0],e[1]=t[1]-n[1],e},normalize:function(e,t){var n=t[0],r=t[1],i=n*n+r*r;return i>0&&(i=1/Math.sqrt(i),e[0]=t[0]*i,e[1]=t[1]*i),e},negate:function(e,t){return e[0]=-t[0],e[1]=-t[1],e},copy:function(e,t){return e[0]=t[0],e[1]=t[1],e},set:function(e,t,n){return e[0]=t,e[1]=n,e}};function t(){this.subRegions=[],this.nSubRegions=0,this.node=null,this.mass=0,this.centerOfMass=null,this.bbox=new Float32Array(4),this.size=0}var n=t.prototype;n.beforeUpdate=function(){for(var e=0;e<this.nSubRegions;e++)this.subRegions[e].beforeUpdate();this.mass=0,this.centerOfMass&&(this.centerOfMass[0]=0,this.centerOfMass[1]=0),this.nSubRegions=0,this.node=null},n.afterUpdate=function(){this.subRegions.length=this.nSubRegions;for(var e=0;e<this.nSubRegions;e++)this.subRegions[e].afterUpdate()},n.addNode=function(e){if(this.nSubRegions===0)if(this.node==null){this.node=e;return}else this._addNodeToSubRegion(this.node),this.node=null;this._addNodeToSubRegion(e),this._updateCenterOfMass(e)},n.findSubRegion=function(e,t){for(var n=0;n<this.nSubRegions;n++){var r=this.subRegions[n];if(r.contain(e,t))return r}},n.contain=function(e,t){return this.bbox[0]<=e&&this.bbox[2]>=e&&this.bbox[1]<=t&&this.bbox[3]>=t},n.setBBox=function(e,t,n,r){this.bbox[0]=e,this.bbox[1]=t,this.bbox[2]=n,this.bbox[3]=r,this.size=(n-e+r-t)/2},n._newSubRegion=function(){var e=this.subRegions[this.nSubRegions];return e||(e=new t,this.subRegions[this.nSubRegions]=e),this.nSubRegions++,e},n._addNodeToSubRegion=function(e){var t=this.findSubRegion(e.position[0],e.position[1]),n=this.bbox;if(!t){var r=(n[0]+n[2])/2,i=(n[1]+n[3])/2,a=(n[2]-n[0])/2,o=(n[3]-n[1])/2,s=+(e.position[0]>=r),c=+(e.position[1]>=i),t=this._newSubRegion();t.setBBox(s*a+n[0],c*o+n[1],(s+1)*a+n[0],(c+1)*o+n[1])}t.addNode(e)},n._updateCenterOfMass=function(e){this.centerOfMass==null&&(this.centerOfMass=new Float32Array(2));var t=this.centerOfMass[0]*this.mass,n=this.centerOfMass[1]*this.mass;t+=e.position[0]*e.mass,n+=e.position[1]*e.mass,this.mass+=e.mass,this.centerOfMass[0]=t/this.mass,this.centerOfMass[1]=n/this.mass};function r(){this.position=new Float32Array(2),this.force=e.create(),this.forcePrev=e.create(),this.mass=1,this.inDegree=0,this.outDegree=0}function i(e,t){this.source=e,this.target=t,this.weight=1}function a(){this.autoSettings=!0,this.barnesHutOptimize=!0,this.barnesHutTheta=1.5,this.repulsionByDegree=!0,this.linLogMode=!1,this.strongGravityMode=!1,this.gravity=1,this.scaling=1,this.edgeWeightInfluence=1,this.jitterTolerence=.1,this.preventOverlap=!1,this.dissuadeHubs=!1,this.rootRegion=new t,this.rootRegion.centerOfMass=e.create(),this.nodes=[],this.edges=[],this.bbox=new Float32Array(4),this.gravityCenter=null,this._massArr=null,this._swingingArr=null,this._sizeArr=null,this._globalSpeed=0}var o=a.prototype;o.initNodes=function(e,t,n){var i=t.length;this.nodes.length=0;for(var a=n!==void 0,o=0;o<i;o++){var s=new r;s.position[0]=e[o*2],s.position[1]=e[o*2+1],s.mass=t[o],a&&(s.size=n[o]),this.nodes.push(s)}this._massArr=t,this._swingingArr=new Float32Array(i),a&&(this._sizeArr=n)},o.initEdges=function(e,t){var n=e.length/2;this.edges.length=0;for(var r=0;r<n;r++){var a=e[r*2],o=e[r*2+1],s=this.nodes[a],c=this.nodes[o];if(!s||!c){console.error(`Node not exists, try initNodes before initEdges`);return}s.outDegree++,c.inDegree++;var l=new i(s,c);t&&(l.weight=t[r]),this.edges.push(l)}},o.updateSettings=function(){if(this.repulsionByDegree)for(var e=0;e<this.nodes.length;e++){var t=this.nodes[e];t.mass=t.inDegree+t.outDegree+1}else for(var e=0;e<this.nodes.length;e++){var t=this.nodes[e];t.mass=this._massArr[e]}},o.update=function(){var t=this.nodes.length;if(this.updateSettings(),this.updateBBox(),this.barnesHutOptimize){this.rootRegion.setBBox(this.bbox[0],this.bbox[1],this.bbox[2],this.bbox[3]),this.rootRegion.beforeUpdate();for(var n=0;n<t;n++)this.rootRegion.addNode(this.nodes[n]);this.rootRegion.afterUpdate()}for(var n=0;n<t;n++){var r=this.nodes[n];e.copy(r.forcePrev,r.force),e.set(r.force,0,0)}for(var n=0;n<t;n++){var i=this.nodes[n];if(this.barnesHutOptimize)this.applyRegionToNodeRepulsion(this.rootRegion,i);else for(var a=n+1;a<t;a++){var o=this.nodes[a];this.applyNodeToNodeRepulsion(i,o,!1)}this.gravity>0&&(this.strongGravityMode?this.applyNodeStrongGravity(i):this.applyNodeGravity(i))}for(var n=0;n<this.edges.length;n++)this.applyEdgeAttraction(this.edges[n]);for(var s=0,c=0,l=e.create(),n=0;n<t;n++){var r=this.nodes[n],u=e.dist(r.force,r.forcePrev);s+=u*r.mass,e.add(l,r.force,r.forcePrev);var d=e.len(l)*.5;c+=d*r.mass,this._swingingArr[n]=u}var f=this.jitterTolerence*this.jitterTolerence*c/s;this._globalSpeed>0&&(f=Math.min(f/this._globalSpeed,1.5)*this._globalSpeed),this._globalSpeed=f;for(var n=0;n<t;n++){var r=this.nodes[n],u=this._swingingArr[n],p=.1*f/(1+f*Math.sqrt(u)),m=e.len(r.force);m>0&&(p=Math.min(m*p,10)/m,e.scaleAndAdd(r.position,r.position,r.force,p))}},o.applyRegionToNodeRepulsion=function(){var t=e.create();return function(n,r){if(n.node)this.applyNodeToNodeRepulsion(n.node,r,!0);else{e.sub(t,r.position,n.centerOfMass);var i=t[0]*t[0]+t[1]*t[1];if(i>this.barnesHutTheta*n.size*n.size){var a=this.scaling*r.mass*n.mass/i;e.scaleAndAdd(r.force,r.force,t,a)}else for(var o=0;o<n.nSubRegions;o++)this.applyRegionToNodeRepulsion(n.subRegions[o],r)}}}(),o.applyNodeToNodeRepulsion=function(){var t=e.create();return function(n,r,i){if(n!=r){e.sub(t,n.position,r.position);var a=t[0]*t[0]+t[1]*t[1];if(a!==0){var o;if(this.preventOverlap){var s=Math.sqrt(a);if(s=s-n.size-r.size,s>0)o=this.scaling*n.mass*r.mass/(s*s);else if(s<0)o=this.scaling*100*n.mass*r.mass;else return}else o=this.scaling*n.mass*r.mass/a;e.scaleAndAdd(n.force,n.force,t,o),e.scaleAndAdd(r.force,r.force,t,-o)}}}}(),o.applyEdgeAttraction=function(){var t=e.create();return function(n){var r=n.source,i=n.target;e.sub(t,r.position,i.position);var a=e.len(t),o=this.edgeWeightInfluence===0?1:this.edgeWeightInfluence===1?n.weight:n.weight**+this.edgeWeightInfluence,s;this.preventOverlap&&(a=a-r.size-i.size,a<=0)||(s=this.linLogMode?-o*Math.log(a+1)/(a+1):-o,e.scaleAndAdd(r.force,r.force,t,s),e.scaleAndAdd(i.force,i.force,t,-s))}}(),o.applyNodeGravity=function(){var t=e.create();return function(n){e.sub(t,this.gravityCenter,n.position);var r=e.len(t);e.scaleAndAdd(n.force,n.force,t,this.gravity*n.mass/(r+1))}}(),o.applyNodeStrongGravity=function(){var t=e.create();return function(n){e.sub(t,this.gravityCenter,n.position),e.scaleAndAdd(n.force,n.force,t,this.gravity*n.mass)}}(),o.updateBBox=function(){for(var e=1/0,t=1/0,n=-1/0,r=-1/0,i=0;i<this.nodes.length;i++){var a=this.nodes[i].position;e=Math.min(e,a[0]),t=Math.min(t,a[1]),n=Math.max(n,a[0]),r=Math.max(r,a[1])}this.bbox[0]=e,this.bbox[1]=t,this.bbox[2]=n,this.bbox[3]=r},o.getGlobalSpeed=function(){return this._globalSpeed};var s=null;self.onmessage=function(e){switch(e.data.cmd){case`init`:s=new a,s.initNodes(e.data.nodesPosition,e.data.nodesMass,e.data.nodesSize),s.initEdges(e.data.edges,e.data.edgesWeight);break;case`updateConfig`:if(s)for(var t in e.data.config)s[t]=e.data.config[t];break;case`update`:var n=e.data.steps;if(s){for(var r=0;r<n;r++)s.update();for(var i=s.nodes.length,o=new Float32Array(i*2),r=0;r<i;r++){var c=s.nodes[r];o[r*2]=c.position[0],o[r*2+1]=c.position[1]}self.postMessage({buffer:o.buffer,globalSpeed:s.getGlobalSpeed()},[o.buffer])}else{var l=new Float32Array;self.postMessage({buffer:l.buffer,globalSpeed:s.getGlobalSpeed()},[l.buffer])}break}}}var vd=_d.toString();vd=vd.slice(vd.indexOf(`{`)+1,vd.lastIndexOf(`}`));var yd={barnesHutOptimize:!0,barnesHutTheta:1.5,repulsionByDegree:!0,linLogMode:!1,strongGravityMode:!1,gravity:1,scaling:1,edgeWeightInfluence:1,jitterTolerence:.1,preventOverlap:!1,dissuadeHubs:!1,gravityCenter:null},bd=function(e){for(var t in yd)this[t]=yd[t];if(e)for(var t in e)this[t]=e[t];this._nodes=[],this._edges=[],this._disposed=!1,this._positionTex=new J({type:q.FLOAT,flipY:!1,minFilter:q.NEAREST,magFilter:q.NEAREST})};bd.prototype.initData=function(e,t){var n=new Blob([vd]),r=window.URL.createObjectURL(n);this._worker=new Worker(r),this._worker.onmessage=this._$onupdate.bind(this),this._nodes=e,this._edges=t,this._frame=0;for(var i=e.length,a=t.length,o=new Float32Array(i*2),s=new Float32Array(i),c=new Float32Array(i),l=new Float32Array(a*2),u=new Float32Array(a),d=0;d<e.length;d++){var f=e[d];o[d*2]=f.x,o[d*2+1]=f.y,s[d]=f.mass==null?1:f.mass,c[d]=f.size==null?1:f.size}for(var d=0;d<t.length;d++){var p=t[d],m=p.node1,h=p.node2;l[d*2]=m,l[d*2+1]=h,u[d]=p.weight==null?1:p.weight}var g=Math.ceil(Math.sqrt(e.length)),_=g,v=new Float32Array(g*_*4),y=this._positionTex;y.width=g,y.height=_,y.pixels=v,this._worker.postMessage({cmd:`init`,nodesPosition:o,nodesMass:s,nodesSize:c,edges:l,edgesWeight:u}),this._globalSpeed=1/0},bd.prototype.updateOption=function(e){var t={};for(var n in yd)t[n]=yd[n];var r=this._nodes,i=this._edges,a=r.length;if(a>5e4?t.jitterTolerence=10:a>5e3?t.jitterTolerence=1:t.jitterTolerence=.1,a>100?t.scaling=2:t.scaling=10,a>1e3?t.barnesHutOptimize=!0:t.barnesHutOptimize=!1,e)for(var n in yd)e[n]!=null&&(t[n]=e[n]);if(!t.gravityCenter){for(var o=[1/0,1/0],s=[-1/0,-1/0],c=0;c<r.length;c++)o[0]=Math.min(r[c].x,o[0]),o[1]=Math.min(r[c].y,o[1]),s[0]=Math.max(r[c].x,s[0]),s[1]=Math.max(r[c].y,s[1]);t.gravityCenter=[(o[0]+s[0])*.5,(o[1]+s[1])*.5]}for(var c=0;c<i.length;c++){var l=i[c].node1,u=i[c].node2;r[l].degree=(r[l].degree||0)+1,r[u].degree=(r[u].degree||0)+1}this._worker&&this._worker.postMessage({cmd:`updateConfig`,config:t})},bd.prototype.update=function(e,t,n){t==null&&(t=1),t=Math.max(t,1),this._frame+=t,this._onupdate=n,this._worker&&this._worker.postMessage({cmd:`update`,steps:Math.round(t)})},bd.prototype._$onupdate=function(e){if(!this._disposed){var t=new Float32Array(e.data.buffer);this._globalSpeed=e.data.globalSpeed,this._positionArr=t,this._updateTexture(t),this._onupdate&&this._onupdate()}},bd.prototype.getNodePositionTexture=function(){return this._positionTex},bd.prototype.getNodeUV=function(e,t){t=t||[];var n=this._positionTex.width,r=this._positionTex.height;return t[0]=e%n/(n-1),t[1]=Math.floor(e/n)/(r-1),t},bd.prototype.getNodes=function(){return this._nodes},bd.prototype.getEdges=function(){return this._edges},bd.prototype.isFinished=function(e){return this._frame>e},bd.prototype.getNodePosition=function(e,t){if(t||(t=new Float32Array(this._nodes.length*2)),this._positionArr)for(var n=0;n<this._positionArr.length;n++)t[n]=this._positionArr[n];return t},bd.prototype._updateTexture=function(e){for(var t=this._positionTex.pixels,n=0,r=0;r<e.length;)t[n++]=e[r++],t[n++]=e[r++],t[n++]=1,t[n++]=1;this._positionTex.dirty()},bd.prototype.dispose=function(e){this._disposed=!0,this._worker=null};var xd=Fe.extend(function(){return{zr:null,viewGL:null,minZoom:.2,maxZoom:5,_needsUpdate:!1,_dx:0,_dy:0,_zoom:1}},function(){this._mouseDownHandler=this._mouseDownHandler.bind(this),this._mouseWheelHandler=this._mouseWheelHandler.bind(this),this._mouseMoveHandler=this._mouseMoveHandler.bind(this),this._mouseUpHandler=this._mouseUpHandler.bind(this),this._update=this._update.bind(this)},{init:function(){var e=this.zr;e.on(`mousedown`,this._mouseDownHandler),e.on(`mousewheel`,this._mouseWheelHandler),e.on(`globalout`,this._mouseUpHandler),e.animation.on(`frame`,this._update)},setTarget:function(e){this._target=e},setZoom:function(e){this._zoom=Math.max(Math.min(e,this.maxZoom),this.minZoom),this._needsUpdate=!0},setOffset:function(e){this._dx=e[0],this._dy=e[1],this._needsUpdate=!0},getZoom:function(){return this._zoom},getOffset:function(){return[this._dx,this._dy]},_update:function(){if(this._target&&this._needsUpdate){var e=this._target,t=this._zoom;e.position.x=this._dx,e.position.y=this._dy,e.scale.set(t,t,t),this.zr.refresh(),this._needsUpdate=!1,this.trigger(`update`)}},_mouseDownHandler:function(e){if(!e.target){var t=e.offsetX,n=e.offsetY;if(!(this.viewGL&&!this.viewGL.containPoint(t,n))){this.zr.on(`mousemove`,this._mouseMoveHandler),this.zr.on(`mouseup`,this._mouseUpHandler);var r=this._convertPos(t,n);this._x=r.x,this._y=r.y}}},_convertPos:function(e,t){var n=this.viewGL.camera,r=this.viewGL.viewport;return{x:(e-r.x)/r.width*(n.right-n.left)+n.left,y:(t-r.y)/r.height*(n.bottom-n.top)+n.top}},_mouseMoveHandler:function(e){var t=this._convertPos(e.offsetX,e.offsetY);this._dx+=t.x-this._x,this._dy+=t.y-this._y,this._x=t.x,this._y=t.y,this._needsUpdate=!0},_mouseUpHandler:function(e){this.zr.off(`mousemove`,this._mouseMoveHandler),this.zr.off(`mouseup`,this._mouseUpHandler)},_mouseWheelHandler:function(e){e=e.event;var t=e.wheelDelta||-e.detail;if(t!==0){var n=e.offsetX,r=e.offsetY;if(!(this.viewGL&&!this.viewGL.containPoint(n,r))){var i=t>0?1.1:.9,a=Math.max(Math.min(this._zoom*i,this.maxZoom),this.minZoom);i=a/this._zoom;var o=this._convertPos(n,r),s=(o.x-this._dx)*(i-1),c=(o.y-this._dy)*(i-1);this._dx-=s,this._dy-=c,this._zoom=a,this._needsUpdate=!0}}},dispose:function(){var e=this.zr;e.off(`mousedown`,this._mouseDownHandler),e.off(`mousemove`,this._mouseMoveHandler),e.off(`mouseup`,this._mouseUpHandler),e.off(`mousewheel`,this._mouseWheelHandler),e.off(`globalout`,this._mouseUpHandler),e.animation.off(`frame`,this._update)}}),Sd=`@export ecgl.lines2D.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

attribute vec2 position: POSITION;
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;

#ifdef POSITIONTEXTURE_ENABLED
uniform sampler2D positionTexture;
#endif

void main()
{
 gl_Position = worldViewProjection * vec4(position, -10.0, 1.0);

 v_Color = a_Color;
}

@end

@export ecgl.lines2D.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

varying vec4 v_Color;

void main()
{
 gl_FragColor = color * v_Color;
}
@end


@export ecgl.meshLines2D.vertex

attribute vec2 position: POSITION;
attribute vec2 normal;
attribute float offset;
attribute vec4 a_Color : COLOR;

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;

varying vec4 v_Color;
varying float v_Miter;

void main()
{
 vec4 p2 = worldViewProjection * vec4(position + normal, -10.0, 1.0);
 gl_Position = worldViewProjection * vec4(position, -10.0, 1.0);

 p2.xy /= p2.w;
 gl_Position.xy /= gl_Position.w;

 vec2 N = normalize(p2.xy - gl_Position.xy);
 gl_Position.xy += N * offset / viewport.zw * 2.0;

 gl_Position.xy *= gl_Position.w;

 v_Color = a_Color;
}
@end


@export ecgl.meshLines2D.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

varying vec4 v_Color;
varying float v_Miter;

void main()
{
 gl_FragColor = color * v_Color;
}

@end`,Cd=Ea.vec2;Q.Shader.import(Sd);var wd=1,Td=d.extend({type:`graphGL`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this.viewGL=new ns(`orthographic`),this.viewGL.camera.left=this.viewGL.camera.right=0,this.viewGL.add(this.groupGL),this._pointsBuilder=new gu(!0,t),this._forceEdgesMesh=new Q.Mesh({material:new Q.Material({shader:Q.createShader(`ecgl.forceAtlas2.edges`),transparent:!0,depthMask:!1,depthTest:!1}),$ignorePicking:!0,geometry:new Q.Geometry({attributes:{node:new Q.Geometry.Attribute(`node`,`float`,2),color:new Q.Geometry.Attribute(`color`,`float`,4,`COLOR`)},dynamic:!0,mainAttribute:`node`}),renderOrder:-1,mode:Q.Mesh.LINES}),this._edgesMesh=new Q.Mesh({material:new Q.Material({shader:Q.createShader(`ecgl.meshLines2D`),transparent:!0,depthMask:!1,depthTest:!1}),$ignorePicking:!0,geometry:new md({useNativeLine:!1,dynamic:!0}),renderOrder:-1,culling:!1}),this._layoutId=0,this._control=new xd({zr:t.getZr(),viewGL:this.viewGL}),this._control.setTarget(this.groupGL),this._control.init(),this._clickHandler=this._clickHandler.bind(this)},render:function(e,t,n){this.groupGL.add(this._pointsBuilder.rootNode),this._model=e,this._api=n,this._initLayout(e,t,n),this._pointsBuilder.update(e,t,n),this._forceLayoutInstance instanceof gd||this.groupGL.remove(this._forceEdgesMesh),this._updateCamera(e,n),this._control.off(`update`),this._control.on(`update`,function(){n.dispatchAction({type:`graphGLRoam`,seriesId:e.id,zoom:this._control.getZoom(),offset:this._control.getOffset()}),this._pointsBuilder.updateView(this.viewGL.camera)},this),this._control.setZoom(X.firstNotNull(e.get(`zoom`),1)),this._control.setOffset(e.get(`offset`)||[0,0]);var r=this._pointsBuilder.getPointsMesh();if(r.off(`mousemove`,this._mousemoveHandler),r.off(`mouseout`,this._mouseOutHandler,this),n.getZr().off(`click`,this._clickHandler),this._pointsBuilder.highlightOnMouseover=!0,e.get(`focusNodeAdjacency`)){var i=e.get(`focusNodeAdjacencyOn`);i===`click`?n.getZr().on(`click`,this._clickHandler):i===`mouseover`&&(r.on(`mousemove`,this._mousemoveHandler,this),r.on(`mouseout`,this._mouseOutHandler,this),this._pointsBuilder.highlightOnMouseover=!1)}this._lastMouseOverDataIndex=-1},_clickHandler:function(e){if(!this._layouting){var t=this._pointsBuilder.getPointsMesh().dataIndex;t>=0?this._api.dispatchAction({type:`graphGLFocusNodeAdjacency`,seriesId:this._model.id,dataIndex:t}):this._api.dispatchAction({type:`graphGLUnfocusNodeAdjacency`,seriesId:this._model.id})}},_mousemoveHandler:function(e){if(!this._layouting){var t=this._pointsBuilder.getPointsMesh().dataIndex;t>=0?t!==this._lastMouseOverDataIndex&&this._api.dispatchAction({type:`graphGLFocusNodeAdjacency`,seriesId:this._model.id,dataIndex:t}):this._mouseOutHandler(e),this._lastMouseOverDataIndex=t}},_mouseOutHandler:function(e){this._layouting||(this._api.dispatchAction({type:`graphGLUnfocusNodeAdjacency`,seriesId:this._model.id}),this._lastMouseOverDataIndex=-1)},_updateForceEdgesGeometry:function(e,t){var n=this._forceEdgesMesh.geometry,r=t.getEdgeData(),i=0,a=this._forceLayoutInstance,o=r.count()*2;n.attributes.node.init(o),n.attributes.color.init(o),r.each(function(t){var o=e[t];n.attributes.node.set(i,a.getNodeUV(o.node1)),n.attributes.node.set(i+1,a.getNodeUV(o.node2));var s=cc(r,o.dataIndex),c=Q.parseColor(s);c[3]*=X.firstNotNull(lc(r,o.dataIndex),1),n.attributes.color.set(i,c),n.attributes.color.set(i+1,c),i+=2}),n.dirty()},_updateMeshLinesGeometry:function(){var e=this._model.getEdgeData(),t=this._edgesMesh.geometry,e=this._model.getEdgeData(),n=this._model.getData().getLayout(`points`);t.resetOffset(),t.setVertexCount(e.count()*t.getLineVertexCount()),t.setTriangleCount(e.count()*t.getLineTriangleCount());var r=[],i=[],a=[`lineStyle`,`width`];this._originalEdgeColors=new Float32Array(e.count()*4),this._edgeIndicesMap=new Float32Array(e.count()),e.each(function(o){var s=e.graph.getEdgeByIndex(o),c=s.node1.dataIndex*2,l=s.node2.dataIndex*2;r[0]=n[c],r[1]=n[c+1],i[0]=n[l],i[1]=n[l+1];var u=cc(e,s.dataIndex),d=Q.parseColor(u);d[3]*=X.firstNotNull(lc(e,s.dataIndex),1);var f=e.getItemModel(s.dataIndex),p=X.firstNotNull(f.get(a),1)*this._api.getDevicePixelRatio();t.addLine(r,i,d,p);for(var m=0;m<4;m++)this._originalEdgeColors[s.dataIndex*4+m]=d[m];this._edgeIndicesMap[s.dataIndex]=o},this),t.dirty()},_updateForceNodesGeometry:function(e){for(var t=this._pointsBuilder.getPointsMesh(),n=[],r=0;r<e.count();r++)this._forceLayoutInstance.getNodeUV(r,n),t.geometry.attributes.position.set(r,n);t.geometry.dirty(`position`)},_initLayout:function(e,t,n){var r=e.get(`layout`),i=e.getGraph(),a=E(e.getBoxLayoutParams(),{width:n.getWidth(),height:n.getHeight()});r===`force`&&(r=`forceAtlas2`),this.stopLayout(e,t,n,{beforeLayout:!0});var o=e.getData(),s=e.getData();if(r===`forceAtlas2`){var c=e.getModel(`forceAtlas2`),l=this._forceLayoutInstance,u=[],d=[],f=o.getDataExtent(`value`),p=s.getDataExtent(`value`),m=X.firstNotNull(c.get(`edgeWeight`),1),h=X.firstNotNull(c.get(`nodeWeight`),1);typeof m==`number`&&(m=[m,m]),typeof h==`number`&&(h=[h,h]);var g=0,_={},v=new Float32Array(o.count()*2);if(i.eachNode(function(e){var t=e.dataIndex,n=o.get(`value`,t),r,i;if(o.hasItemOption){var s=o.getItemModel(t);r=s.get(`x`),i=s.get(`y`)}r==null&&(r=a.x+Math.random()*a.width,i=a.y+Math.random()*a.height),v[g*2]=r,v[g*2+1]=i,_[e.id]=g++;var c=M(n,f,h);isNaN(c)&&(c=isNaN(h[0])?1:h[0]),u.push({x:r,y:i,mass:c,size:o.getItemVisual(t,`symbolSize`)})}),o.setLayout(`points`,v),i.eachEdge(function(e){var t=e.dataIndex,n=M(o.get(`value`,t),p,m);isNaN(n)&&(n=isNaN(m[0])?1:m[0]),d.push({node1:_[e.node1.id],node2:_[e.node2.id],weight:n,dataIndex:t})}),!l){var y=c.get(`GPU`);this._forceLayoutInstance&&(y&&!(this._forceLayoutInstance instanceof gd)||!y&&!(this._forceLayoutInstance instanceof bd))&&(this._forceLayoutInstanceToDispose=this._forceLayoutInstance),l=this._forceLayoutInstance=y?new gd:new bd}l.initData(u,d),l.updateOption(c.option),this._updateForceEdgesGeometry(l.getEdges(),e),this._updatePositionTexture(),n.dispatchAction({type:`graphGLStartLayout`,from:this.uid})}else{var v=new Float32Array(o.count()*2),g=0;i.eachNode(function(e){var t=e.dataIndex,n,r;if(o.hasItemOption){var i=o.getItemModel(t);n=i.get(`x`),r=i.get(`y`)}v[g++]=n,v[g++]=r}),o.setLayout(`points`,v),this._updateAfterLayout(e,t,n)}},_updatePositionTexture:function(){var e=this._forceLayoutInstance.getNodePositionTexture();this._pointsBuilder.setPositionTexture(e),this._forceEdgesMesh.material.set(`positionTex`,e)},startLayout:function(e,t,n,r){if(!(r&&r.from!=null&&r.from!==this.uid)){var i=this.viewGL,n=this._api,a=this._forceLayoutInstance,o=this._model.getData(),s=this._model.getModel(`forceAtlas2`);if(a&&(this.groupGL.remove(this._edgesMesh),this.groupGL.add(this._forceEdgesMesh),this._forceLayoutInstance)){this._updateForceNodesGeometry(e.getData()),this._pointsBuilder.hideLabels();var c=this,l=this._layoutId=wd++,u=s.getShallow(`maxSteps`),d=s.getShallow(`steps`),f=0,p=Math.max(d*2,20),m=function(t){if(t===c._layoutId){if(a.isFinished(u)){n.dispatchAction({type:`graphGLStopLayout`,from:c.uid}),n.dispatchAction({type:`graphGLFinishLayout`,points:o.getLayout(`points`),from:c.uid});return}a.update(i.layer.renderer,d,function(){c._updatePositionTexture(),f+=d,f>=p&&(c._syncNodePosition(e),f=0),n.getZr().refresh(),P(function(){m(t)})})}};P(function(){c._forceLayoutInstanceToDispose&&(c._forceLayoutInstanceToDispose.dispose(i.layer.renderer),c._forceLayoutInstanceToDispose=null),m(l)}),this._layouting=!0}}},stopLayout:function(e,t,n,r){r&&r.from!=null&&r.from!==this.uid||(this._layoutId=0,this.groupGL.remove(this._forceEdgesMesh),this.groupGL.add(this._edgesMesh),this._forceLayoutInstance&&this.viewGL.layer&&(r&&r.beforeLayout||(this._syncNodePosition(e),this._updateAfterLayout(e,t,n)),this._api.getZr().refresh(),this._layouting=!1))},_syncNodePosition:function(e){var t=this._forceLayoutInstance.getNodePosition(this.viewGL.layer.renderer);e.getData().setLayout(`points`,t),e.setNodePosition(t)},_updateAfterLayout:function(e,t,n){this._updateMeshLinesGeometry(),this._pointsBuilder.removePositionTexture(),this._pointsBuilder.updateLayout(e,t,n),this._pointsBuilder.updateView(this.viewGL.camera),this._pointsBuilder.updateLabels(),this._pointsBuilder.showLabels()},focusNodeAdjacency:function(e,t,n,r){var i=this._model.getData();this._downplayAll();var a=r.dataIndex,o=i.graph,s=[],c=o.getNodeByIndex(a);s.push(c),c.edges.forEach(function(e){e.dataIndex<0||(e.node1!==c&&s.push(e.node1),e.node2!==c&&s.push(e.node2))},this),this._pointsBuilder.fadeOutAll(.05),this._fadeOutEdgesAll(.05),s.forEach(function(e){this._pointsBuilder.highlight(i,e.dataIndex)},this),this._pointsBuilder.updateLabels(s.map(function(e){return e.dataIndex}));var l=[];c.edges.forEach(function(e){e.dataIndex>=0&&(this._highlightEdge(e.dataIndex),l.push(e))},this),this._focusNodes=s,this._focusEdges=l},unfocusNodeAdjacency:function(e,t,n,r){this._downplayAll(),this._pointsBuilder.fadeInAll(),this._fadeInEdgesAll(),this._pointsBuilder.updateLabels()},_highlightEdge:function(e){var t=this._model.getEdgeData().getItemModel(e),n=Q.parseColor(t.get(`emphasis.lineStyle.color`)||t.get(`lineStyle.color`)),r=X.firstNotNull(t.get(`emphasis.lineStyle.opacity`),t.get(`lineStyle.opacity`),1);n[3]*=r,this._edgesMesh.geometry.setItemColor(this._edgeIndicesMap[e],n)},_downplayAll:function(){this._focusNodes&&this._focusNodes.forEach(function(e){this._pointsBuilder.downplay(this._model.getData(),e.dataIndex)},this),this._focusEdges&&this._focusEdges.forEach(function(e){this._downplayEdge(e.dataIndex)},this)},_downplayEdge:function(e){var t=this._getColor(e,[]);this._edgesMesh.geometry.setItemColor(this._edgeIndicesMap[e],t)},_setEdgeFade:function(){var e=[];return function(t,n){this._getColor(t,e),e[3]*=n,this._edgesMesh.geometry.setItemColor(this._edgeIndicesMap[t],e)}}(),_getColor:function(e,t){for(var n=0;n<4;n++)t[n]=this._originalEdgeColors[e*4+n];return t},_fadeOutEdgesAll:function(e){this._model.getData().graph.eachEdge(function(t){this._setEdgeFade(t.dataIndex,e)},this)},_fadeInEdgesAll:function(){this._fadeOutEdgesAll(1)},_updateCamera:function(e,t){this.viewGL.setViewport(0,0,t.getWidth(),t.getHeight(),t.getDevicePixelRatio());for(var n=this.viewGL.camera,r=e.getData().getLayout(`points`),i=Cd.create(1/0,1/0),a=Cd.create(-1/0,-1/0),o=[],s=0;s<r.length;)o[0]=r[s++],o[1]=r[s++],Cd.min(i,i,o),Cd.max(a,a,o);var c=(a[1]+i[1])/2,l=(a[0]+i[0])/2;if(!(l>n.left&&l<n.right&&c<n.bottom&&c>n.top)){var u=Math.max(a[0]-i[0],10),d=u/t.getWidth()*t.getHeight();u*=1.4,d*=1.4,i[0]-=u*.2,n.left=i[0],n.top=c-d/2,n.bottom=c+d/2,n.right=u+i[0],n.near=0,n.far=100}},dispose:function(){var e=this.viewGL.layer.renderer;this._forceLayoutInstance&&this._forceLayoutInstance.dispose(e),this.groupGL.removeAll(),this._layoutId=-1,this._pointsBuilder.dispose()},remove:function(){this.groupGL.removeAll(),this._control.dispose()}}),Ed=pe;function Dd(e){return e instanceof Array||(e=[e,e]),e}function Od(e){ma(Ed,`ForceAtlas2`,bd),ma(Ed,`ForceAtlas2GPU`,gd),e.registerChartView(Td),e.registerSeriesModel(dd),e.registerVisual(function(e){let t={};e.eachSeriesByType(`graphGL`,function(e){var n=e.getCategoriesData(),r=e.getData(),i={};n.each(function(r){var a=n.getName(r);i[`ec-`+a]=r;var o=n.getItemModel(r),s=o.getModel(`itemStyle`).getItemStyle();s.fill||(s.fill=e.getColorFromPalette(a,t)),n.setItemVisual(r,`style`,s);var c=[`symbol`,`symbolSize`,`symbolKeepAspect`];for(let e=0;e<c.length;e++){var l=o.getShallow(c[e],!0);l!=null&&n.setItemVisual(r,c[e],l)}}),n.count()&&r.each(function(e){let t=r.getItemModel(e).getShallow(`category`);if(t!=null){typeof t==`string`&&(t=i[`ec-`+t]);var a=n.getItemVisual(t,`style`),o=r.ensureUniqueItemVisual(e,`style`);Ed.util.extend(o,a);var s=[`symbol`,`symbolSize`,`symbolKeepAspect`];for(let i=0;i<s.length;i++)r.setItemVisual(e,s[i],n.getItemVisual(t,s[i]))}})})}),e.registerVisual(function(e){e.eachSeriesByType(`graphGL`,function(e){var t=e.getGraph(),n=e.getEdgeData(),r=Dd(e.get(`edgeSymbol`)),i=Dd(e.get(`edgeSymbolSize`));n.setVisual(`drawType`,`stroke`),n.setVisual(`fromSymbol`,r&&r[0]),n.setVisual(`toSymbol`,r&&r[1]),n.setVisual(`fromSymbolSize`,i&&i[0]),n.setVisual(`toSymbolSize`,i&&i[1]),n.setVisual(`style`,e.getModel(`lineStyle`).getLineStyle()),n.each(function(e){var r=n.getItemModel(e),i=t.getEdgeByIndex(e),a=Dd(r.getShallow(`symbol`,!0)),o=Dd(r.getShallow(`symbolSize`,!0)),s=r.getModel(`lineStyle`).getLineStyle(),c=n.ensureUniqueItemVisual(e,`style`);switch(Ed.util.extend(c,s),c.stroke){case`source`:var l=i.node1.getVisual(`style`);c.stroke=l&&l.fill;break;case`target`:var l=i.node2.getVisual(`style`);c.stroke=l&&l.fill;break}a[0]&&i.setVisual(`fromSymbol`,a[0]),a[1]&&i.setVisual(`toSymbol`,a[1]),o[0]&&i.setVisual(`fromSymbolSize`,o[0]),o[1]&&i.setVisual(`toSymbolSize`,o[1])})})}),e.registerAction({type:`graphGLRoam`,event:`graphglroam`,update:`series.graphGL:roam`},function(e,t){t.eachComponent({mainType:`series`,query:e},function(t){t.setView(e)})});function t(){}e.registerAction({type:`graphGLStartLayout`,event:`graphgllayoutstarted`,update:`series.graphGL:startLayout`},t),e.registerAction({type:`graphGLStopLayout`,event:`graphgllayoutstopped`,update:`series.graphGL:stopLayout`},t),e.registerAction({type:`graphGLFocusNodeAdjacency`,event:`graphGLFocusNodeAdjacency`,update:`series.graphGL:focusNodeAdjacency`},t),e.registerAction({type:`graphGLUnfocusNodeAdjacency`,event:`graphGLUnfocusNodeAdjacency`,update:`series.graphGL:unfocusNodeAdjacency`},t)}h(Od);var kd=u.extend({type:`series.flowGL`,dependencies:[`geo`,`grid`,`bmap`],visualStyleAccessPath:`itemStyle`,getInitialData:function(e,t){var r=this.get(`coordinateSystem`),i=r===`geo`?[`lng`,`lat`]:w(r)||[`x`,`y`];i.push(`vx`,`vy`);var a=new n(Te(this.getSource(),{coordDimensions:i,encodeDefine:this.get(`encode`),dimensionsDefine:this.get(`dimensions`)}),this);return a.initData(this.getSource()),a},defaultOption:{coordinateSystem:`cartesian2d`,zlevel:10,supersampling:1,particleType:`point`,particleDensity:128,particleSize:1,particleSpeed:1,particleTrail:2,colorTexture:null,gridWidth:`auto`,gridHeight:`auto`,itemStyle:{color:`#fff`,opacity:.8}}}),Ad=Y.extend(function(){return{dynamic:!0,attributes:{position:new Y.Attribute(`position`,`float`,3,`POSITION`)}}},{resetOffset:function(){this._vertexOffset=0,this._faceOffset=0},setLineCount:function(e){var t=this.attributes,n=4*e,r=2*e;this.vertexCount!==n&&t.position.init(n),this.triangleCount!==r&&(r===0?this.indices=null:this.indices=this.vertexCount>65535?new Uint32Array(r*3):new Uint16Array(r*3))},addLine:function(e){var t=this._vertexOffset;this.attributes.position.set(t,[e[0],e[1],1]),this.attributes.position.set(t+1,[e[0],e[1],-1]),this.attributes.position.set(t+2,[e[0],e[1],2]),this.attributes.position.set(t+3,[e[0],e[1],-2]),this.setTriangleIndices(this._faceOffset++,[t,t+1,t+2]),this.setTriangleIndices(this._faceOffset++,[t+1,t+2,t+3]),this._vertexOffset+=4}});K.import(`@export ecgl.vfParticle.particle.fragment

uniform sampler2D particleTexture;
uniform sampler2D spawnTexture;
uniform sampler2D velocityTexture;

uniform float deltaTime;
uniform float elapsedTime;

uniform float speedScaling : 1.0;

uniform vec2 textureSize;
uniform vec4 region : [0, 0, 1, 1];
uniform float firstFrameTime;

varying vec2 v_Texcoord;


void main()
{
 vec4 p = texture2D(particleTexture, v_Texcoord);
 bool spawn = false;
 if (p.w <= 0.0) {
 p = texture2D(spawnTexture, fract(v_Texcoord + elapsedTime / 10.0));
 p.w -= firstFrameTime;
 spawn = true;
 }
 vec2 v = texture2D(velocityTexture, fract(p.xy * region.zw + region.xy)).xy;
 v = (v - 0.5) * 2.0;
 p.z = length(v);
 p.xy += v * deltaTime / 10.0 * speedScaling;
 p.w -= deltaTime;

 if (spawn || p.xy != fract(p.xy)) {
 p.z = 0.0;
 }
 p.xy = fract(p.xy);

 gl_FragColor = p;
}
@end

@export ecgl.vfParticle.renderPoints.vertex

#define PI 3.1415926

attribute vec2 texcoord : TEXCOORD_0;

uniform sampler2D particleTexture;
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

uniform float size : 1.0;

varying float v_Mag;
varying vec2 v_Uv;

void main()
{
 vec4 p = texture2D(particleTexture, texcoord);

 if (p.w > 0.0 && p.z > 1e-5) {
 gl_Position = worldViewProjection * vec4(p.xy * 2.0 - 1.0, 0.0, 1.0);
 }
 else {
 gl_Position = vec4(100000.0, 100000.0, 100000.0, 1.0);
 }

 v_Mag = p.z;
 v_Uv = p.xy;

 gl_PointSize = size;
}

@end

@export ecgl.vfParticle.renderPoints.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];
uniform sampler2D gradientTexture;
uniform sampler2D colorTexture;
uniform sampler2D spriteTexture;

varying float v_Mag;
varying vec2 v_Uv;

void main()
{
 gl_FragColor = color;
#ifdef SPRITETEXTURE_ENABLED
 gl_FragColor *= texture2D(spriteTexture, gl_PointCoord);
 if (color.a == 0.0) {
 discard;
 }
#endif
#ifdef GRADIENTTEXTURE_ENABLED
 gl_FragColor *= texture2D(gradientTexture, vec2(v_Mag, 0.5));
#endif
#ifdef COLORTEXTURE_ENABLED
 gl_FragColor *= texture2D(colorTexture, v_Uv);
#endif
}

@end

@export ecgl.vfParticle.renderLines.vertex

#define PI 3.1415926

attribute vec3 position : POSITION;

uniform sampler2D particleTexture;
uniform sampler2D prevParticleTexture;

uniform float size : 1.0;
uniform vec4 vp: VIEWPORT;
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

varying float v_Mag;
varying vec2 v_Uv;

@import clay.util.rand

void main()
{
 vec4 p = texture2D(particleTexture, position.xy);
 vec4 p2 = texture2D(prevParticleTexture, position.xy);

 p.xy = p.xy * 2.0 - 1.0;
 p2.xy = p2.xy * 2.0 - 1.0;

 if (p.w > 0.0 && p.z > 1e-5) {
 vec2 dir = normalize(p.xy - p2.xy);
 vec2 norm = vec2(dir.y / vp.z, -dir.x / vp.w) * sign(position.z) * size;
 if (abs(position.z) == 2.0) {
 gl_Position = vec4(p.xy + norm, 0.0, 1.0);
 v_Uv = p.xy;
 v_Mag = p.z;
 }
 else {
 gl_Position = vec4(p2.xy + norm, 0.0, 1.0);
 v_Mag = p2.z;
 v_Uv = p2.xy;
 }
 gl_Position = worldViewProjection * gl_Position;
 }
 else {
 gl_Position = vec4(100000.0, 100000.0, 100000.0, 1.0);
 }
}

@end

@export ecgl.vfParticle.renderLines.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];
uniform sampler2D gradientTexture;
uniform sampler2D colorTexture;

varying float v_Mag;
varying vec2 v_Uv;

void main()
{
 gl_FragColor = color;
 #ifdef GRADIENTTEXTURE_ENABLED
 gl_FragColor *= texture2D(gradientTexture, vec2(v_Mag, 0.5));
#endif
#ifdef COLORTEXTURE_ENABLED
 gl_FragColor *= texture2D(colorTexture, v_Uv);
#endif
}

@end
`);function jd(e){var t=document.createElement(`canvas`);t.width=t.height=e;var n=t.getContext(`2d`);return n.fillStyle=`#fff`,n.arc(e/2,e/2,e/2,0,Math.PI*2),n.fill(),t}var Md=function(){this.motionBlurFactor=.99,this.vectorFieldTexture=new J({type:q.FLOAT,flipY:!1}),this.particleLife=[5,20],this._particleType=`point`,this._particleSize=1,this.particleColor=[1,1,1,1],this.particleSpeedScaling=1,this._thisFrameTexture=null,this._particlePass=null,this._spawnTexture=null,this._particleTexture0=null,this._particleTexture1=null,this._particlePointsMesh=null,this._surfaceFrameBuffer=null,this._elapsedTime=0,this._scene=null,this._camera=null,this._lastFrameTexture=null,this._supersampling=1,this._downsampleTextures=[],this._width=512,this._height=512,this.init()};Md.prototype={constructor:Md,init:function(){var e={type:q.FLOAT,minFilter:q.NEAREST,magFilter:q.NEAREST,useMipmap:!1};this._spawnTexture=new J(e),this._particleTexture0=new J(e),this._particleTexture1=new J(e),this._frameBuffer=new Or({depthBuffer:!1}),this._particlePass=new bi({fragment:K.source(`ecgl.vfParticle.particle.fragment`)}),this._particlePass.setUniform(`velocityTexture`,this.vectorFieldTexture),this._particlePass.setUniform(`spawnTexture`,this._spawnTexture),this._downsamplePass=new bi({fragment:K.source(`clay.compositor.downsample`)});var t=new tt({renderOrder:10,material:new Mt({shader:new K(K.source(`ecgl.vfParticle.renderPoints.vertex`),K.source(`ecgl.vfParticle.renderPoints.fragment`))}),mode:tt.POINTS,geometry:new Y({dynamic:!0,mainAttribute:`texcoord0`})}),n=new tt({renderOrder:10,material:new Mt({shader:new K(K.source(`ecgl.vfParticle.renderLines.vertex`),K.source(`ecgl.vfParticle.renderLines.fragment`))}),geometry:new Ad,culling:!1}),r=new tt({material:new Mt({shader:new K(K.source(`ecgl.color.vertex`),K.source(`ecgl.color.fragment`))}),geometry:new jr});r.material.enableTexture(`diffuseMap`),this._particlePointsMesh=t,this._particleLinesMesh=n,this._lastFrameFullQuadMesh=r,this._camera=new _i,this._thisFrameTexture=new J,this._lastFrameTexture=new J},setParticleDensity:function(e,t){for(var n=e*t,r=new Float32Array(n*4),i=0,a=this.particleLife,o=0;o<e;o++)for(var s=0;s<t;s++,i++){r[i*4]=Math.random(),r[i*4+1]=Math.random(),r[i*4+2]=Math.random();var c=(a[1]-a[0])*Math.random()+a[0];r[i*4+3]=c}this._particleType===`line`?this._setLineGeometry(e,t):this._setPointsGeometry(e,t),this._spawnTexture.width=e,this._spawnTexture.height=t,this._spawnTexture.pixels=r,this._particleTexture0.width=this._particleTexture1.width=e,this._particleTexture0.height=this._particleTexture1.height=t,this._particlePass.setUniform(`textureSize`,[e,t])},_setPointsGeometry:function(e,t){var n=e*t,r=this._particlePointsMesh.geometry,i=r.attributes;i.texcoord0.init(n);for(var a=0,o=0;o<e;o++)for(var s=0;s<t;s++,a++)i.texcoord0.value[a*2]=o/e,i.texcoord0.value[a*2+1]=s/t;r.dirty()},_setLineGeometry:function(e,t){var n=e*t,r=this._getParticleMesh().geometry;r.setLineCount(n),r.resetOffset();for(var i=0;i<e;i++)for(var a=0;a<t;a++)r.addLine([i/e,a/t]);r.dirty()},_getParticleMesh:function(){return this._particleType===`line`?this._particleLinesMesh:this._particlePointsMesh},update:function(e,t,n,r){var i=this._getParticleMesh(),a=this._frameBuffer,o=this._particlePass;r&&this._updateDownsampleTextures(e,t),i.material.set(`size`,this._particleSize*this._supersampling),i.material.set(`color`,this.particleColor),o.setUniform(`speedScaling`,this.particleSpeedScaling),a.attach(this._particleTexture1),o.setUniform(`firstFrameTime`,r?(this.particleLife[1]+this.particleLife[0])/2:0),o.setUniform(`particleTexture`,this._particleTexture0),o.setUniform(`deltaTime`,n),o.setUniform(`elapsedTime`,this._elapsedTime),o.render(e,a),i.material.set(`particleTexture`,this._particleTexture1),i.material.set(`prevParticleTexture`,this._particleTexture0),a.attach(this._thisFrameTexture),a.bind(e),e.gl.clear(e.gl.DEPTH_BUFFER_BIT|e.gl.COLOR_BUFFER_BIT);var s=this._lastFrameFullQuadMesh;s.material.set(`diffuseMap`,this._lastFrameTexture),s.material.set(`color`,[1,1,1,this.motionBlurFactor]),this._camera.update(!0),e.renderPass([s,i],this._camera),a.unbind(e),this._downsample(e),this._swapTexture(),this._elapsedTime+=n},_downsample:function(e){var t=this._downsampleTextures;if(t.length!==0)for(var n=0,r=this._thisFrameTexture,i=t[n];i;)this._frameBuffer.attach(i),this._downsamplePass.setUniform(`texture`,r),this._downsamplePass.setUniform(`textureSize`,[r.width,r.height]),this._downsamplePass.render(e,this._frameBuffer),r=i,i=t[++n]},getSurfaceTexture:function(){var e=this._downsampleTextures;return e.length>0?e[e.length-1]:this._lastFrameTexture},setRegion:function(e){this._particlePass.setUniform(`region`,e)},resize:function(e,t){this._lastFrameTexture.width=e*this._supersampling,this._lastFrameTexture.height=t*this._supersampling,this._thisFrameTexture.width=e*this._supersampling,this._thisFrameTexture.height=t*this._supersampling,this._width=e,this._height=t},setParticleSize:function(e){var t=this._getParticleMesh();if(e<=2){t.material.disableTexture(`spriteTexture`),t.material.transparent=!1;return}this._spriteTexture||(this._spriteTexture=new J),(!this._spriteTexture.image||this._spriteTexture.image.width!==e)&&(this._spriteTexture.image=jd(e),this._spriteTexture.dirty()),t.material.transparent=!0,t.material.enableTexture(`spriteTexture`),t.material.set(`spriteTexture`,this._spriteTexture),this._particleSize=e},setGradientTexture:function(e){var t=this._getParticleMesh().material;t[e?`enableTexture`:`disableTexture`](`gradientTexture`),t.setUniform(`gradientTexture`,e)},setColorTextureImage:function(e,t){this._getParticleMesh().material.setTextureImage(`colorTexture`,e,t,{flipY:!0})},setParticleType:function(e){this._particleType=e},clearFrame:function(e){var t=this._frameBuffer;t.attach(this._lastFrameTexture),t.bind(e),e.gl.clear(e.gl.DEPTH_BUFFER_BIT|e.gl.COLOR_BUFFER_BIT),t.unbind(e)},setSupersampling:function(e){this._supersampling=e,this.resize(this._width,this._height)},_updateDownsampleTextures:function(e,t){for(var n=this._downsampleTextures,r=Math.max(Math.floor(Math.log(this._supersampling/t.getDevicePixelRatio())/Math.log(2)),0),i=2,a=this._width*this._supersampling,o=this._height*this._supersampling,s=0;s<r;s++)n[s]=n[s]||new J,n[s].width=a/i,n[s].height=o/i,i*=2;for(;s<n.length;s++)n[s].dispose(e);n.length=r},_swapTexture:function(){var e=this._particleTexture0;this._particleTexture0=this._particleTexture1,this._particleTexture1=e;var e=this._thisFrameTexture;this._thisFrameTexture=this._lastFrameTexture,this._lastFrameTexture=e},dispose:function(e){e.disposeFrameBuffer(this._frameBuffer),e.disposeTexture(this.vectorFieldTexture),e.disposeTexture(this._spawnTexture),e.disposeTexture(this._particleTexture0),e.disposeTexture(this._particleTexture1),e.disposeTexture(this._thisFrameTexture),e.disposeTexture(this._lastFrameTexture),e.disposeGeometry(this._particleLinesMesh.geometry),e.disposeGeometry(this._particlePointsMesh.geometry),e.disposeGeometry(this._lastFrameFullQuadMesh.geometry),this._spriteTexture&&e.disposeTexture(this._spriteTexture),this._particlePass.dispose(e),this._downsamplePass.dispose(e),this._downsampleTextures.forEach(function(t){t.dispose(e)})}};var Nd=d.extend({type:`flowGL`,__ecgl__:!0,init:function(e,t){this.viewGL=new ns(`orthographic`),this.groupGL=new Q.Node,this.viewGL.add(this.groupGL),this._particleSurface=new Md;var n=new Q.Mesh({geometry:new Q.PlaneGeometry,material:new Q.Material({shader:new Q.Shader({vertex:Q.Shader.source(`ecgl.color.vertex`),fragment:Q.Shader.source(`ecgl.color.fragment`)}),transparent:!0})});n.material.enableTexture(`diffuseMap`),this.groupGL.add(n),this._planeMesh=n},render:function(e,t,n){var r=this._particleSurface;r.setParticleType(e.get(`particleType`)),r.setSupersampling(e.get(`supersampling`)),this._updateData(e,n),this._updateCamera(n.getWidth(),n.getHeight(),n.getDevicePixelRatio());var i=X.firstNotNull(e.get(`particleDensity`),128);r.setParticleDensity(i,i);var a=this._planeMesh,o=+new Date,s=this,c=!0;a.__percent=0,a.stopAnimation(),a.animate(``,{loop:!0}).when(1e5,{__percent:1}).during(function(){var e=+new Date,t=Math.min(e-o,20);o+=t,s._renderer&&(r.update(s._renderer,n,t/1e3,c),a.material.set(`diffuseMap`,r.getSurfaceTexture())),c=!1}).start();var l=e.getModel(`itemStyle`),u=Q.parseColor(l.get(`color`));u[3]*=X.firstNotNull(l.get(`opacity`),1),a.material.set(`color`,u),r.setColorTextureImage(e.get(`colorTexture`),n),r.setParticleSize(e.get(`particleSize`)),r.particleSpeedScaling=e.get(`particleSpeed`),r.motionBlurFactor=1-.1**e.get(`particleTrail`)},updateTransform:function(e,t,n){this._updateData(e,n)},afterRender:function(e,t,n,r){var i=r.renderer;this._renderer=i},_updateData:function(e,t){var n=e.coordinateSystem,r=n.dimensions.map(function(t){return e.coordDimToDataDim(t)[0]}),i=e.getData(),a=i.getDataExtent(r[0]),o=i.getDataExtent(r[1]),s=e.get(`gridWidth`),c=e.get(`gridHeight`);if(s==null||s===`auto`){var l=(a[1]-a[0])/(o[1]-o[0]);s=Math.round(Math.sqrt(l*i.count()))}(c==null||c===`auto`)&&(c=Math.ceil(i.count()/s));var u=this._particleSurface.vectorFieldTexture,d=u.pixels;if(!d||d.length!==c*s*4)d=u.pixels=new Float32Array(s*c*4);else for(var f=0;f<d.length;f++)d[f]=0;var p=0,m=1/0,h=new Float32Array(i.count()*2),g=0,_=[[1/0,1/0],[-1/0,-1/0]];i.each([r[0],r[1],`vx`,`vy`],function(e,t,r,i){var a=n.dataToPoint([e,t]);h[g++]=a[0],h[g++]=a[1],_[0][0]=Math.min(a[0],_[0][0]),_[0][1]=Math.min(a[1],_[0][1]),_[1][0]=Math.max(a[0],_[1][0]),_[1][1]=Math.max(a[1],_[1][1]);var o=Math.sqrt(r*r+i*i);p=Math.max(p,o),m=Math.min(m,o)}),i.each([`vx`,`vy`],function(e,t,n){var r=Math.round((h[n*2]-_[0][0])/(_[1][0]-_[0][0])*(s-1)),i=((c-1-Math.round((h[n*2+1]-_[0][1])/(_[1][1]-_[0][1])*(c-1)))*s+r)*4;d[i]=e/p*.5+.5,d[i+1]=t/p*.5+.5,d[i+3]=1}),u.width=s,u.height=c,e.get(`coordinateSystem`)===`bmap`&&this._fillEmptyPixels(u),u.dirty(),this._updatePlanePosition(_[0],_[1],e,t),this._updateGradientTexture(i.getVisual(`visualMeta`),[m,p])},_fillEmptyPixels:function(e){var t=e.pixels,n=e.width,r=e.height;function i(e,i,a){e=Math.max(Math.min(e,n-1),0),i=Math.max(Math.min(i,r-1),0);var o=(i*(n-1)+e)*4;return t[o+3]===0?!1:(a[0]=t[o],a[1]=t[o+1],!0)}function a(e,t,n){n[0]=e[0]+t[0],n[1]=e[1]+t[1]}for(var o=[],s=[],c=[],l=[],u=[],d=0,f=0;f<r;f++)for(var p=0;p<n;p++){var m=(f*(n-1)+p)*4;t[m+3]===0&&(d=o[0]=o[1]=0,i(p-1,f,s)&&(d++,a(s,o,o)),i(p+1,f,c)&&(d++,a(c,o,o)),i(p,f-1,l)&&(d++,a(l,o,o)),i(p,f+1,u)&&(d++,a(u,o,o)),o[0]/=d,o[1]/=d,t[m]=o[0],t[m+1]=o[1]),t[m+3]=1}},_updateGradientTexture:function(e,t){if(!e||!e.length){this._particleSurface.setGradientTexture(null);return}this._gradientTexture=this._gradientTexture||new Q.Texture2D({image:document.createElement(`canvas`)});var n=this._gradientTexture,r=n.image;r.width=200,r.height=1;var i=r.getContext(`2d`),a=i.createLinearGradient(0,.5,r.width,.5);e[0].stops.forEach(function(e){var n;t[1]===t[0]?n=0:(n=e.value/t[1],n=Math.min(Math.max(n,0),1)),a.addColorStop(n,e.color)}),i.fillStyle=a,i.fillRect(0,0,r.width,r.height),n.dirty(),this._particleSurface.setGradientTexture(this._gradientTexture)},_updatePlanePosition:function(e,t,n,r){var i=this._limitInViewportAndFullFill(e,t,n,r);e=i.leftTop,t=i.rightBottom,this._particleSurface.setRegion(i.region),this._planeMesh.position.set((e[0]+t[0])/2,r.getHeight()-(e[1]+t[1])/2,0);var a=t[0]-e[0],o=t[1]-e[1];this._planeMesh.scale.set(a/2,o/2,1),this._particleSurface.resize(Math.max(Math.min(a,2048),1),Math.max(Math.min(o,2048),1)),this._renderer&&this._particleSurface.clearFrame(this._renderer)},_limitInViewportAndFullFill:function(e,t,n,r){var i=[Math.max(e[0],0),Math.max(e[1],0)],a=[Math.min(t[0],r.getWidth()),Math.min(t[1],r.getHeight())];if(n.get(`coordinateSystem`)===`bmap`){var o=n.getData().getDataExtent(n.coordDimToDataDim(`lng`)[0]);Math.floor(o[1]-o[0])>=359&&(i[0]>0&&(i[0]=0),a[0]<r.getWidth()&&(a[0]=r.getWidth()))}var s=t[0]-e[0],c=t[1]-e[1],l=a[0]-i[0],u=a[1]-i[1];return{leftTop:i,rightBottom:a,region:[(i[0]-e[0])/s,1-u/c-(i[1]-e[1])/c,l/s,u/c]}},_updateCamera:function(e,t,n){this.viewGL.setViewport(0,0,e,t,n);var r=this.viewGL.camera;r.left=r.bottom=0,r.top=t,r.right=e,r.near=0,r.far=100,r.position.z=10},remove:function(){this._planeMesh.stopAnimation(),this.groupGL.removeAll()},dispose:function(){this._renderer&&this._particleSurface.dispose(this._renderer),this.groupGL.removeAll()}});function Pd(e){e.registerChartView(Nd),e.registerSeriesModel(kd)}h(Pd);var Fd=u.extend({type:`series.linesGL`,dependencies:[`grid`,`geo`],visualStyleAccessPath:`lineStyle`,visualDrawType:`stroke`,streamEnabled:!0,init:function(e){var t=this._processFlatCoordsArray(e.data);this._flatCoords=t.flatCoords,this._flatCoordsOffset=t.flatCoordsOffset,t.flatCoords&&(e.data=new Float32Array(t.count)),Fd.superApply(this,`init`,arguments)},mergeOption:function(e){var t=this._processFlatCoordsArray(e.data);this._flatCoords=t.flatCoords,this._flatCoordsOffset=t.flatCoordsOffset,t.flatCoords&&(e.data=new Float32Array(t.count)),Fd.superApply(this,`mergeOption`,arguments)},appendData:function(e){var t=this._processFlatCoordsArray(e.data);t.flatCoords&&(this._flatCoords?(this._flatCoords=r(this._flatCoords,t.flatCoords),this._flatCoordsOffset=r(this._flatCoordsOffset,t.flatCoordsOffset)):(this._flatCoords=t.flatCoords,this._flatCoordsOffset=t.flatCoordsOffset),e.data=new Float32Array(t.count)),this.getRawData().appendData(e.data)},_getCoordsFromItemModel:function(e){var t=this.getData().getItemModel(e);return t.option instanceof Array?t.option:t.getShallow(`coords`)},getLineCoordsCount:function(e){return this._flatCoordsOffset?this._flatCoordsOffset[e*2+1]:this._getCoordsFromItemModel(e).length},getLineCoords:function(e,t){if(this._flatCoordsOffset){for(var n=this._flatCoordsOffset[e*2],r=this._flatCoordsOffset[e*2+1],i=0;i<r;i++)t[i]=t[i]||[],t[i][0]=this._flatCoords[n+i*2],t[i][1]=this._flatCoords[n+i*2+1];return r}else{for(var a=this._getCoordsFromItemModel(e),i=0;i<a.length;i++)t[i]=t[i]||[],t[i][0]=a[i][0],t[i][1]=a[i][1];return a.length}},_processFlatCoordsArray:function(e){var t=0;if(this._flatCoords&&(t=this._flatCoords.length),typeof e[0]==`number`){for(var n=e.length,r=new Uint32Array(n),i=new Float64Array(n),a=0,o=0,s=0,c=0;c<n;){s++;var l=e[c++];r[o++]=a+t,r[o++]=l;for(var u=0;u<l;u++){var d=e[c++],f=e[c++];i[a++]=d,i[a++]=f}}return{flatCoordsOffset:new Uint32Array(r.buffer,0,o),flatCoords:i,count:s}}return{flatCoordsOffset:null,flatCoords:null,count:e.length}},getInitialData:function(e,t){var r=new n([`value`],this);return r.hasItemOption=!1,r.initData(fi(e.data),[],function(e,t,n,i){if(e instanceof Array)return NaN;r.hasItemOption=!0;var a=e.value;if(a!=null)return a instanceof Array?a[i]:a}),r},defaultOption:{coordinateSystem:`geo`,zlevel:10,progressive:1e4,progressiveThreshold:5e4,blendMode:`source-over`,lineStyle:{opacity:.8},postEffect:{enable:!1,colorCorrection:{exposure:0,brightness:0,contrast:1,saturation:1,enable:!0}}}}),Id=d.extend({type:`linesGL`,__ecgl__:!0,init:function(e,t){this.groupGL=new Q.Node,this.viewGL=new ns(`orthographic`),this.viewGL.add(this.groupGL),this._glViewHelper=new sd(this.viewGL),this._nativeLinesShader=Q.createShader(`ecgl.lines3D`),this._meshLinesShader=Q.createShader(`ecgl.meshLines3D`),this._linesMeshes=[],this._currentStep=0},render:function(e,t,n){this.groupGL.removeAll(),this._glViewHelper.reset(e,n);var r=this._linesMeshes[0];r||(r=this._linesMeshes[0]=this._createLinesMesh(e)),this._linesMeshes.length=1,this.groupGL.add(r),this._updateLinesMesh(e,r,0,e.getData().count()),this.viewGL.setPostEffect(e.getModel(`postEffect`),n)},incrementalPrepareRender:function(e,t,n){this.groupGL.removeAll(),this._glViewHelper.reset(e,n),this._currentStep=0,this.viewGL.setPostEffect(e.getModel(`postEffect`),n)},incrementalRender:function(e,t,n,r){var i=this._linesMeshes[this._currentStep];i||(i=this._createLinesMesh(t),this._linesMeshes[this._currentStep]=i),this._updateLinesMesh(t,i,e.start,e.end),this.groupGL.add(i),r.getZr().refresh(),this._currentStep++},updateTransform:function(e,t,n){e.coordinateSystem.getRoamTransform&&this._glViewHelper.updateTransform(e,n)},_createLinesMesh:function(e){return new Q.Mesh({$ignorePicking:!0,material:new Q.Material({shader:Q.createShader(`ecgl.lines3D`),transparent:!0,depthMask:!1,depthTest:!1}),geometry:new md({segmentScale:10,useNativeLine:!0,dynamic:!1}),mode:Q.Mesh.LINES,culling:!1})},_updateLinesMesh:function(e,t,n,r){var i=e.getData();t.material.blend=e.get(`blendMode`)===`lighter`?Q.additiveBlend:null;var a=e.get(`lineStyle.curveness`)||0,o=e.get(`polyline`),s=t.geometry,c=e.coordinateSystem,l=X.firstNotNull(e.get(`lineStyle.width`),1);l>1?(t.material.shader!==this._meshLinesShader&&t.material.attachShader(this._meshLinesShader),t.mode=Q.Mesh.TRIANGLES):(t.material.shader!==this._nativeLinesShader&&t.material.attachShader(this._nativeLinesShader),t.mode=Q.Mesh.LINES),n=n||0,r=r||i.count(),s.resetOffset();var u=0,d=0,f=[],p=[],m=[],h=[],g=[],_=.3,v=.7;function y(){p[0]=f[0]*v+h[0]*_-(f[1]-h[1])*a,p[1]=f[1]*v+h[1]*_-(h[0]-f[0])*a,m[0]=f[0]*_+h[0]*v-(f[1]-h[1])*a,m[1]=f[1]*_+h[1]*v-(h[0]-f[0])*a}if(o||a!==0)for(var b=n;b<r;b++)if(o){var x=e.getLineCoordsCount(b);u+=s.getPolylineVertexCount(x),d+=s.getPolylineTriangleCount(x)}else e.getLineCoords(b,g),this._glViewHelper.dataToPoint(c,g[0],f),this._glViewHelper.dataToPoint(c,g[1],h),y(),u+=s.getCubicCurveVertexCount(f,p,m,h),d+=s.getCubicCurveTriangleCount(f,p,m,h);else{var S=r-n;u+=S*s.getLineVertexCount(),d+=S*s.getLineVertexCount()}s.setVertexCount(u),s.setTriangleCount(d);for(var C=n,w=[],b=n;b<r;b++){Q.parseColor(cc(i,C),w);var T=X.firstNotNull(lc(i,C),1);w[3]*=T;for(var x=e.getLineCoords(b,g),E=0;E<x;E++)this._glViewHelper.dataToPoint(c,g[E],g[E]);o?s.addPolyline(g,w,l,0,x):a===0?s.addPolyline(g,w,l,0,2):(f=g[0],h=g[1],y(),s.addCubicCurve(f,p,m,h,w,l)),C++}},dispose:function(){this.groupGL.removeAll()},remove:function(){this.groupGL.removeAll()}});function Ld(e){e.registerChartView(Id),e.registerSeriesModel(Fd)}h(Ld);