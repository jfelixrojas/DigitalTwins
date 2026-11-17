/* Comparador008 en Chrome real: dos mapas, un reloj, solo loopback. */
const {chromium} = require("playwright");
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict"),crypto=require("node:crypto");
const root=path.resolve(__dirname,".."),out=path.join(root,"outputs/intervention008/browser");
const url=process.env.DT_NICEGUI_URL||"http://127.0.0.1:8087/",origin=new URL(url).origin;
const digest=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
for(const name of ["profile","tmp","downloads"])fs.mkdirSync(path.join(out,name),{recursive:true});
const dataPath=path.join(root,"outputs/nicegui_comparison/data.json"),catalogPath=path.join(root,"outputs/nicegui_comparison/vehicle_catalog.json");
const D=JSON.parse(fs.readFileSync(dataPath,"utf8")),V=JSON.parse(fs.readFileSync(catalogPath,"utf8"));
(async()=>{
  const context=await chromium.launchPersistentContext(path.join(out,"profile"),{
    executablePath:process.env.DT_CHROME_PATH||"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless:true,viewport:{width:1600,height:1100},downloadsPath:path.join(out,"downloads"),env:{...process.env,TMPDIR:path.join(out,"tmp")},
    args:["--no-first-run","--disable-background-networking","--disable-component-update","--disable-sync","--no-default-browser-check"]
  });
  const page=context.pages()[0],checks=[],errors=[],external=[],sent=[],received=[];
  const check=(name,value)=>{assert(value,name);checks.push(name);};
  await context.route("**/*",route=>{
    const target=new URL(route.request().url());
    if(target.protocol.startsWith("http")&&target.origin!==origin){external.push(target.href);return route.abort("internetdisabled");}
    return route.continue();
  });
  page.on("pageerror",error=>errors.push(String(error)));
  page.on("console",message=>{if(message.type()==="error")errors.push(message.text());});
  page.on("websocket",socket=>{
    if(new URL(socket.url()).hostname!=="127.0.0.1")external.push(socket.url());
    socket.on("framesent",e=>{if(String(e.payload).startsWith("42"))sent.push(String(e.payload));});
    socket.on("framereceived",e=>{if(String(e.payload).startsWith("42"))received.push(String(e.payload));});
  });
  const state=()=>page.evaluate(()=>DT008.getState()),inspect=()=>page.evaluate(()=>DT008.inspect());
  const seek=async time=>page.locator("#time-slider").evaluate((node,t)=>{node.value=t;node.dispatchEvent(new Event("input",{bubbles:true}));},time);
  const vehicle=async id=>page.locator("#vehicle-search").fill(id);
  function nativePane(pane,time,scenario){
    if(pane.frameTime!==time||pane.scenario!==scenario)return false;
    const rows=D.frames[scenario][time],byId=new Map(pane.vehicles.map(v=>[v.id,v]));
    return rows.length===byId.size&&rows.every(([idx,lat,lon])=>{
      const v=byId.get(D.vehicles[idx]);return v&&v.lat===lat&&v.lon===lon;
    });
  }
  function both(snapshot){return nativePane(snapshot.panes.primary,snapshot.state.time,"base")&&nativePane(snapshot.panes.secondary,snapshot.state.time,"closure");}
  try{
    await page.goto(url,{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>window.DT008?.getState().ready,null,{timeout:30000});
    check("Initial single mode preserved",(await state()).mode==="single");
    check("One visible map initially",await page.locator(".corridor-map:visible").count()===1);
    check("Native single base positions",nativePane((await inspect()).panes.primary,0,"base"));
    check("No external tiles in either map",Object.values((await inspect()).panes).every(p=>p.tileLayers===0));
    await page.screenshot({path:path.join(out,"01_single_desktop.png"),fullPage:true});
    await seek(480);await page.locator("#mode-compare").click();
    check("Compare preserves instant",(await state()).time===480&&(await state()).mode==="compare");
    check("Two visible maps",await page.locator(".corridor-map:visible").count()===2);
    for(const time of [0,1,50,205,480,836,1799]){
      await seek(time);check("Both panes equal native FCD at"+time,both(await inspect()));
    }
    check("A single clock control",await page.locator("#clock").count()===1&&await page.locator("#time-slider").count()===1);
    check("150 original IDs available",await page.locator("#vehicle-ids option").count()===150);
    check("350 exact edge choices",await page.locator("#edge-select option").count()===350);
    await seek(480);await vehicle("W_E.0020");
    let snapshot=await inspect();
    check("Same selected ID in both panes",snapshot.panes.primary.vehicles.some(v=>v.id==="W_E.0020"&&v.selected)&&snapshot.panes.secondary.vehicles.some(v=>v.id==="W_E.0020"&&v.selected));
    check("Selected routes are executed native routes",JSON.stringify(snapshot.panes.primary.route)===JSON.stringify(V.vehicles["W_E.0020"].base.route)&&JSON.stringify(snapshot.panes.secondary.route)===JSON.stringify(V.vehicles["W_E.0020"].closure.route));
    check("Closed edge open in base and closed in closure",snapshot.panes.primary.closedLabel.includes("abierto")&&snapshot.panes.secondary.closedLabel.includes("Cierre virtual"));
    await page.locator("#locate-vehicle").click();
    check("Locate does not change shared time",(await state()).time===480&&both(await inspect()));
    await page.locator("#fit-map").click();
    await page.screenshot({path:path.join(out,"02_comparison_desktop.png"),fullPage:true});
    await page.locator(".maps-grid").screenshot({path:path.join(out,"03_two_maps.png")});
    await seek(0);
    check("No fabricated position before departure",Object.values((await inspect()).panes).every(p=>!p.vehicles.some(v=>v.id==="W_E.0020"))&&(await page.locator("#vehicle-base-state").innerText()).includes("Aún no"));
    await seek(1799);
    check("No ghost marker after arrival",Object.values((await inspect()).panes).every(p=>p.vehicles.length===0)&&(await page.locator("#vehicle-closure-state").innerText()).includes("finalizado"));
    await seek(500);await vehicle("N_E.0007");snapshot=await inspect();
    check("Indirect case retains same ID",both(snapshot)&&snapshot.selectedVehicle==="N_E.0007");
    check("Individual lifecycle from native tripinfo",(await page.locator("#vehicle-base-trip").innerText()).includes(String(V.vehicles["N_E.0007"].base.duration_s)));
    await page.locator("#edge-select").selectOption("-175606174");
    check("Edge selection shared by both maps",Object.values((await inspect()).panes).every(p=>p.selectedEdge==="-175606174"));
    await vehicle("WRONG-ID");await page.locator("#vehicle-form button[type=submit]").click();
    check("Unknown ID rejected",(await state()).selectedVehicle==="N_E.0007"&&(await page.locator("#vehicle-error").innerText()).includes("ID original"));
    await page.locator("#clear-vehicle").click();
    check("Clear ID removes emphasis",(await state()).selectedVehicle===""&&await page.locator("#vehicle-inspector").isHidden());
    await page.locator(".primary-map .leaflet-control-zoom-in").click();await page.waitForTimeout(350);
    snapshot=await inspect();
    check("Zoom is linked",snapshot.panes.primary.camera.zoom===snapshot.panes.secondary.camera.zoom);
    const rect=await page.locator(".primary-map").boundingBox();
    await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);
    await page.mouse.down();await page.mouse.move(rect.x+rect.width/2+45,rect.y+rect.height/2+20,{steps:8});await page.mouse.up();await page.waitForTimeout(200);
    snapshot=await inspect();
    const cameraPixelDifference=await page.evaluate(()=>{
      const a=getElement(document.querySelector(".primary-map")).map,b=getElement(document.querySelector(".secondary-map")).map;
      return a.project(a.getCenter(),a.getZoom()).distanceTo(a.project(b.getCenter(),a.getZoom()));
    });
    check("Camera centers aligned within one CSS pixel",cameraPixelDifference<=1);
    await page.locator("#fit-map").click();
    check("Native comparison totals visible",(await page.locator("#compare-metrics").innerText()).includes("19,935")&&(await page.locator("#compare-metrics").innerText()).includes("20,340"));
    await page.locator("#chart-delta").click();
    check("OD differences retained",(await inspect()).odSeries.length===1);
    await page.locator("#chart-paired").click();
    await seek(400);await vehicle("W_E.0020");await page.locator("#speed").selectOption("30");
    await page.evaluate(data=>{
      window.__dt8Frames=[];window.__dt8Run=true;window.__dt8Expected=data;
      function sample(){
        if(!window.__dt8Run)return;
        const s=DT008.inspect(),d=window.__dt8Expected,t=s.state.time;
        let valid=s.state.mode==="compare";
        for(const [key,scenario]of[["primary","base"],["secondary","closure"]]){
          const p=s.panes[key],expected=d.frames[scenario][t],actual=new Map(p.vehicles.map(v=>[v.id,v]));
          valid=valid&&p.frameTime===t&&p.scenario===scenario&&actual.size===expected.length&&expected.every(([idx,lat,lon])=>{const v=actual.get(d.vehicles[idx]);return v&&v.lat===lat&&v.lon===lon;});
        }
        window.__dt8Frames.push({t,valid});requestAnimationFrame(sample);
      }
      requestAnimationFrame(sample);
    },D);
    await page.waitForTimeout(180);const beforeSent=sent.length,beforeReceived=received.length;
    await page.locator("#play").click();await page.waitForTimeout(2400);await page.locator("#play").click();
    const sampled=await page.evaluate(()=>{window.__dt8Run=false;return window.__dt8Frames;});
    check("Every observed animation frame synchronized",sampled.length>30&&sampled.every(v=>v.valid));
    check("Shared time advances at30x",(await state()).time>455&&(await state()).time<485);
    const transport={sent:sent.slice(beforeSent),received:received.slice(beforeReceived)};
    check("No Python frame updates",transport.sent.concat(transport.received).every(m=>JSON.parse(m.slice(2))[0]==="ack"));
    const paused=(await state()).time;await page.waitForTimeout(160);check("Pause holds both maps",(await state()).time===paused&&both(await inspect()));
    fs.writeFileSync(path.join(out,"synchronization.json"),JSON.stringify({sampled_frames:sampled,transport},null,2));
    await page.locator("#mode-single").click();
    check("Return to one map keeps time",(await state()).time===paused&&await page.locator(".corridor-map:visible").count()===1);
    await page.locator("#scenario-closure").click();
    check("Single closure still native",nativePane((await inspect()).panes.primary,paused,"closure")&&(await page.locator("#duration-total").innerText()).includes("20,340"));
    await page.locator("#reset").click();check("Single restart still works",(await state()).time===0&&!(await state()).playing);
    await page.locator("#mode-compare").click();await seek(480);await page.locator("#advance").click();
    check("Shared advance ten seconds",(await state()).time===490&&both(await inspect()));
    for(const width of [1024,768,390,320]){
      await page.setViewportSize({width,height:900});await page.waitForTimeout(180);
      check("No horizontal overflow "+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    }
    await page.setViewportSize({width:390,height:900});await page.waitForTimeout(180);
    check("Mobile indicators collapsed",await page.locator("#indicators-panel").evaluate(e=>!e.open));
    check("Mobile analysis collapsed",await page.locator("#analysis-details").evaluate(e=>!e.open));
    await page.locator("#fit-map").click();await seek(480);await vehicle("W_E.0020");
    await page.screenshot({path:path.join(out,"04_comparison_mobile.png"),fullPage:true});
    await page.locator("#indicators-panel > summary").click();
    check("Mobile indicators expand",await page.locator("#compare-metrics").isVisible());
    await page.locator("#analysis-details > summary").click();
    check("Mobile charts expand",await page.locator("#chart-delta").isVisible());
    await page.locator("#chart-delta").click();
    await page.screenshot({path:path.join(out,"05_mobile_analysis.png"),fullPage:true});
    await page.locator("#indicators-panel > summary").click();await page.locator("#analysis-details > summary").click();
    await page.locator("#mode-single").click();
    check("Mobile single scenario control stays visible with indicators collapsed",await page.locator("#scenario-closure").isVisible()&&await page.locator("#indicators-panel").evaluate(e=>!e.open));
    await page.screenshot({path:path.join(out,"06_single_mobile.png"),fullPage:true});
    for(const code of ["SIM-002","SIM-003","SIM-004","SIM-005"]){
      const response=await page.request.get(origin+"/experiment/"+code+".md");
      check("Original ficha "+code,response.ok()&&(await response.text()).includes(code));
    }
    check("No external requests",external.length===0);
    check("No JavaScript errors",errors.length===0);
    check("No runtime error panel",await page.locator("#runtime-error").isHidden());
    const result={pass:true,checked_at_utc:new Date().toISOString(),browser:context.browser().version(),checks,errors,external_requests:external,
      data_sha256:digest(dataPath),vehicle_catalog_sha256:digest(catalogPath),qa_script_sha256:digest(__filename),
      animation_frames_audited:sampled.length,camera_pan_difference_css_px:cameraPixelDifference,diagnostics:(await inspect()).diagnostics};
    fs.writeFileSync(path.join(out,"validation.json"),JSON.stringify(result,null,2)+"\n");
    console.log(JSON.stringify({pass:true,checks:checks.length,animation_frames_audited:sampled.length,diagnostics:result.diagnostics}));
  }catch(error){
    fs.writeFileSync(path.join(out,"failure_state.json"),JSON.stringify(await inspect().catch(()=>null),null,2));
    await page.screenshot({path:path.join(out,"failure.png"),fullPage:true}).catch(()=>{});
    fs.writeFileSync(path.join(out,"validation.json"),JSON.stringify({pass:false,error:String(error),checks,errors,external_requests:external},null,2));throw error;
  }finally{await context.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
