let data = { profiles: [] };
let currentIndex = 0;

const nameInput = document.getElementById("name");
const colorInput = document.getElementById("color");
const reinInput  = document.getElementById("rein");
const outputBox  = document.getElementById("output");

fetch('profiles.json')
  .then(r => r.json())
  .then(j => { data = j; refreshList(); });

const inputTypes = ["Keyboard","MouseButtons","MouseMove","Gamepad","Analog"];
const inputTypesReins = ["Keyboard","Mouse","Gamepad","Analog"];

const actions = ["Tap","Hold","Toggle", "ToggleOn", "ToggleOff","Multitap","Macro"];
const actionsInsideMacro = ["Tap","Hold","Toggle", "ToggleOn", "ToggleOff","Multitap"];

/* Key options per input type */
const keyOptions = {
  Keyboard: [
    "A","B","C","D","E","F","G","H","I","J","K","L","M",
    "N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
    "0","1","2","3","4","5","6","7","8","9",
    "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
    "Space","Enter","Escape","Tab","Backspace","Delete",
    "Left","Right","Up","Down",
    "LCtrl","RCtrl","LShift","RShift","LAlt","RAlt","LWin","RWin"
  ],
  MouseMove: ["X","Y","Wheel"],
  Mouse: ["Left","Right","Middle","Mouse4","Mouse5"],
  MouseButtons: ["Left","Right","Mouse3","Mouse4","Mouse5"],
  Gamepad: [
    "A","B","X","Y","LB","RB","LT","RT",
    "Start","Back","LSB","RSB",
    "DPadUp","DPadDown","DPadLeft","DPadRight"
  ],
  Analog: ["LeftStick X","LeftStick Y","RightStick X","RightStick Y","Trigger L","Trigger R"]
};

/* ---------------- PROFILE LIST ---------------- */

function refreshList(){
  const list = document.getElementById("profileList");
  list.innerHTML = "";
  data.profiles.forEach((p,i)=>{
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = p.Name || "Unnamed";
    list.appendChild(opt);
  });
  list.onchange = ()=>{ currentIndex = parseInt(list.value); loadProfile(); };
  list.value = currentIndex;
  loadProfile();
}

/* ---------------- HELPERS ---------------- */

function rgbToHex(r,g,b){
  return "#" + [r,g,b].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function hexToRgb(hex){
  const v = hex.replace('#','');
  return [parseInt(v.substring(0,2),16), parseInt(v.substring(2,4),16), parseInt(v.substring(4,6),16)];
}
function setDisabled(el, state){
  el.disabled = state;
  el.style.opacity = state ? "0.4" : "1";
}

/* ---------------- LOAD PROFILE ---------------- */

function loadProfile(){
  const p = data.profiles[currentIndex];
  if(!p) return;
  if(!p.Name) p.Name = "Unnamed Profile";
  nameInput.value = p.Name;
  colorInput.value = rgbToHex(...(p["LED Color"] || [255,255,255]));
  buildReinUI(p["Rein Mode"] || []);
  const container = document.getElementById("buttons");
  container.innerHTML = "";
  for(const key in p.Buttons){
    container.appendChild(createButtonUI(key, p.Buttons[key]));
  }
}

/* ---------------- HELPERS ---------------- */

function createSelect(options, value){
  const sel = document.createElement("select");
  options.forEach(o=>{
    const opt = document.createElement("option");
    opt.value = o; opt.textContent = o;
    if(o === value) opt.selected = true;
    sel.appendChild(opt);
  });
  return sel;
}

function createKeySelect(type, value){
  const opts = keyOptions[type] || [];
  const sel = createSelect(opts, value);
  // If value not in list, add it as first option so data isn't lost
  if(value && !opts.includes(value)){
    const opt = document.createElement("option");
    opt.value = value; opt.textContent = value; opt.selected = true;
    sel.insertBefore(opt, sel.firstChild);
  }
  return sel;
}

/* ---------------- BUTTON UI ---------------- */

function createButtonUI(name, config){
  const div = document.createElement("div");
  div.className = "button-block";

  const title = document.createElement("b");
  title.textContent = name;
  title.className = "action"
  div.appendChild(title);

  const isMacroConfig = config[0] === "Macro";
  const typeSel = createSelect(inputTypes, isMacroConfig ? "Keyboard" : config[0]);

  // Key: dropdown, rebuilt when type changes
  let keySel = createKeySelect(typeSel.value, config[1] || "");
  const keyWrapper = document.createElement("span");
  keyWrapper.appendChild(keySel);

  const actionSel = createSelect(actions, isMacroConfig ? "Macro" : (config[2] || "Tap"));


  // Hold / Amount field with label
  const holdLabel = document.createElement("label");
  holdLabel.style.fontSize = "0.8em";
  const holdTime = document.createElement("input");
  holdTime.className = "numberinput";
  holdTime.type = "number";
  holdTime.min = "0";
  holdTime.max = "10";
  holdTime.placeholder = "Seconds";
  holdLabel.appendChild(holdTime);

  const analogLabel = document.createElement("input");
analogLabel.type = "number";     // only numeric input
analogLabel.step = "1";          // integers only
analogLabel.min = "-127";
analogLabel.max = "127";
analogLabel.placeholder = "Analog";
analogLabel.className = "numberinput";
analogLabel.value = config[4] || "";

  const mouseMoveLabel = document.createElement("input");
mouseMoveLabel.type = "number";     // only numeric input
mouseMoveLabel.step = "1";          // integers only
mouseMoveLabel.min = "-9000";
mouseMoveLabel.max = "9000";
mouseMoveLabel.placeholder = "Mouse movement";
mouseMoveLabel.className = "numberinput";
mouseMoveLabel.value = config[4] || "";

  const macroContainer = document.createElement("div");

  // Restore hold/amount value
  holdTime.value = config[3] || "";

  /* --- Rebuild key dropdown when type changes --- */
  function rebuildKeySelect(newType, keepValue){
    const newSel = createKeySelect(newType, keepValue);
    newSel.oninput = update;
    keyWrapper.innerHTML = "";
    keyWrapper.appendChild(newSel);
    keySel = newSel;
  }

  /* --- Visibility --- */
  function updateUI(){
    const isHold      = actionSel.value === "Hold";
    const isMultitap  = actionSel.value === "Multitap";
    const isMacro     = actionSel.value === "Macro";
    const isAnalog  = typeSel.value   === "Analog";
    const isMouseMove  = typeSel.value   === "MouseMove";

    const showHoldField = isHold || isMultitap;
    const showAnalogField = isAnalog || isMouseMove;


    holdLabel.style.display = showHoldField ? "" : "none";
    analogLabel.style.display = showAnalogField ? "" : "none";
    analogLabel.placeholder = isMouseMove ? "Movement" : "Movement";
    holdTime.placeholder = isMultitap ? "Tap amount" : "Hold time";

      if (isMacro) {
    keySel.value = config[1]?.[0]?.[1] || ""; // or keep original
  }


    setDisabled(typeSel, isMacro);
    setDisabled(keySel, isMacro);
  }

  /* --- Update data --- */
  function update(){
    const profile  = data.profiles[currentIndex];
    const joystick = analogLabel.value || "";
    const mousemove = analogLabel.value || "";
    let newConfig;

    if(actionSel.value === "Macro"){
      newConfig = (config[0] === "Macro")
        ? config
        : ["Macro", [[typeSel.value, keySel.value, "Tap"]], null, null, joystick];
    } else {
      newConfig = [typeSel.value, keySel.value, actionSel.value];
      if(actionSel.value === "Hold" || actionSel.value === "Multitap"){
        newConfig.push(holdTime.value || 0);
      }
      newConfig[4] = joystick || mousemove;
    }

    profile.Buttons[name] = newConfig;
    config = newConfig;
    updateUI();
    renderMacro();
  }

  /* --- Macro rendering --- */
  function renderMacro(){
    macroContainer.innerHTML = "";
    if(actionSel.value !== "Macro") return;
    const steps = config[1] || [];
    steps.forEach((step,i)=>{
      macroContainer.appendChild(createMacroStep(name, i, step));
    });
    const addBtn = document.createElement("button");
    addBtn.textContent = "Add Step";
    addBtn.onclick = ()=>{
      steps.push(["Keyboard","A","Tap","0","0"]);
      config[1] = steps;
      update();
      loadProfile();
    };
    macroContainer.appendChild(addBtn);
  }

  /* --- Events --- */
  typeSel.onchange = ()=>{
    rebuildKeySelect(typeSel.value, "");
    update();
  };
  actionSel.onchange = update;
  holdTime.oninput   = update;
  analogLabel.oninput = update;
  // keySel.oninput set inside rebuildKeySelect; set initial one too
  keySel.oninput = update;

  div.appendChild(typeSel);
  div.appendChild(keyWrapper);
  div.appendChild(actionSel);
  div.appendChild(holdLabel);
  div.appendChild(analogLabel);
  div.appendChild(macroContainer);

  updateUI();
  renderMacro();

  return div;
}

/* ---------------- MACRO STEP ---------------- */

function createMacroStep(buttonName, index, step){
  const row = document.createElement("div");
 
  row.className = "macro-step";

  const type = createSelect(inputTypes, step[0]);
  let key = createKeySelect(type.value, step[1] || "");
  const keyWrapper = document.createElement("span");
  keyWrapper.appendChild(key);

  const act  = createSelect(actionsInsideMacro, step[2]);

  const holdLabel = document.createElement("input");
  holdLabel.style.fontSize = "0.8em";
  const hold = document.createElement("input");
  hold.className = "numberinput";
  hold.type = "number";
  holdLabel.min = "0";
  holdLabel.appendChild(hold);
  if(step[3]) hold.value = step[3];

  const analogLabel = document.createElement("input");
  analogLabel.placeholder = "Joystick Axis";
  analogLabel.className = "numberinput";
  analogLabel.value = step[4] || "";

  function updateStepUI(){
    const isHold     = act.value === "Hold";
    const isMultitap = act.value === "Multitap";
    const isAnalog = type.value === "Analog";
    const isMouseMove = type.value === "MouseMove";
    const showHold   = isHold || isMultitap;
    const showAnalog = isAnalog || isMouseMove

    holdLabel.style.display = showHold ? "" : "none";
    holdLabel.childNodes[0].textContent = isMultitap ? "Amount: " : "Hold ms: ";
    analogLabel.style.display = showAnalog ? "" : "none";
    analogLabel.placeholder = isMouseMove ? "Movement" : "Movement";
    holdLabel.placeholder = isMouseMove ? "Tap amount" : "Hold time";
    


  }

  function rebuildKeySelect(newType, keepValue){
    const newSel = createKeySelect(newType, keepValue);
    newSel.oninput = sync;
    keyWrapper.innerHTML = "";
    keyWrapper.appendChild(newSel);
    key = newSel;
  }

  function sync(){
    const arr = [type.value, key.value, act.value];
    if(act.value === "Hold" || act.value === "Multitap") arr.push(hold.value || 0);
    arr[4] = analogLabel.value || "";
    data.profiles[currentIndex].Buttons[buttonName][1][index] = arr;
    updateStepUI();
  }

  type.onchange = ()=>{ rebuildKeySelect(type.value, ""); sync(); };
  act.onchange  = ()=>{ sync(); loadProfile(); };
  key.oninput = hold.oninput = analogLabel.oninput = sync;

  const del = document.createElement("button");
  del.textContent = "Remove step";
  del.onclick = ()=>{
    data.profiles[currentIndex].Buttons[buttonName][1].splice(index,1);
    loadProfile();
  };

  row.appendChild(type);
  row.appendChild(keyWrapper);  // key dropdown
  row.appendChild(act);
  row.appendChild(holdLabel);   // hold/amount (label + input)
  row.appendChild(analogLabel); // joystick field — was missing!
  row.appendChild(del);

  updateStepUI();
  return row;
}

/* ---------------- PROFILE INPUTS ---------------- */

nameInput.oninput  = e=>{ data.profiles[currentIndex].Name = e.target.value; };
colorInput.oninput = e=>{ data.profiles[currentIndex]["LED Color"] = hexToRgb(e.target.value); };

/* ---------------- PROFILE MGMT ---------------- */

function addProfile(){
  data.profiles.push({ id: 4, Name: "New Profile", "LED Color": [255,255,255], "Rein Mode": [], Buttons: {"Start Moving": ["Keyboard","W","Tap"],"Start Moving2": ["Keyboard","W","Tap"],"Start Moving3": ["Keyboard","W","Tap"],"Start Moving": ["Keyboard","W","Tap"]} });
  refreshList();
}
function deleteProfile(){
  const confirmDelete = confirm("Do you want to delete this profile?");

  if (!confirmDelete) return;

  data.profiles.splice(currentIndex, 1);
  currentIndex = 0;
  refreshList();
}
function reviewJSON(){
  outputBox.value = JSON.stringify(data,null,2);
}

const modeRules = {
  Keyboard: { keys: true, hold: false },
  Mouse:    { keys: false, hold: true },
  Analog:   { keys: false, hold: true },
  Gamepad:   { keys: true, hold: false }
};

function buildReinUI(values = []) {
  const container = document.getElementById("reinContainer");
  container.innerHTML = "";

  // ---------- STATE ----------
  let state = {
    mode: values[0] || "Mouse",
    key1: values[1] || "",
    key2: values[2] || "",
    hold: values[3] || "Hold Off"
  };

  // ---------- CONTROLS ----------
  const mode = createSelect(inputTypesReins, state.mode);

  let key1 = createKeySelect(mode.value, state.key1);
  let key2 = createKeySelect(mode.value, state.key2);

  const key1Wrapper = document.createElement("span");
  const key2Wrapper = document.createElement("span");

  key1Wrapper.appendChild(key1);
  key2Wrapper.appendChild(key2);

  const hold = createSelect(["Hold On", "Hold Off"], state.hold);

  // ---------- UPDATE STATE ----------
  function sync() {
    state.mode = mode.value;
    state.key1 = key1.value;
    state.key2 = key2.value;
    state.hold = hold.value;

    data.profiles[currentIndex]["Rein Mode"] = [
      state.mode,
      state.key1,
      state.key2,
      state.hold
    ];

    updateUI();
  }

  // ---------- REBUILD KEYS ONLY WHEN MODE CHANGES ----------
  function rebuildKeys() {
    const newKey1 = createKeySelect(mode.value, "");
    const newKey2 = createKeySelect(mode.value, "");

    newKey1.oninput = sync;
    newKey2.oninput = sync;

    key1Wrapper.innerHTML = "";
    key2Wrapper.innerHTML = "";

    key1Wrapper.appendChild(newKey1);
    key2Wrapper.appendChild(newKey2);

    key1 = newKey1;
    key2 = newKey2;
  }

  // ---------- MODE RULE ENGINE ----------
  function updateUI() {
    const rule = modeRules[mode.value] || {};

    key1.disabled = !rule.keys;
    key2.disabled = !rule.keys;
    hold.disabled = !rule.hold;

    const dim = (el, d) => el.style.opacity = d ? "0.4" : "1";

    dim(key1, !rule.keys);
    dim(key2, !rule.keys);
  }

  // ---------- EVENTS ----------
  mode.onchange = () => {
    rebuildKeys();
    sync();
  };

  key1.oninput = sync;
  key2.oninput = sync;
  hold.onchange = sync;

  // ---------- BUILD UI ----------
  container.appendChild(makeField("Mode", mode));
  container.appendChild(makeField("Turn left", key1Wrapper));
  container.appendChild(makeField("Turn right", key2Wrapper));
  container.appendChild(makeField("Hold", hold));

  updateUI();
}

function makeField(title, element) {
  const wrapper = document.createElement("div");
  wrapper.className = "field";

  const label = document.createElement("div");
  label.className = "field-title";
  label.textContent = title;

  wrapper.appendChild(label);
  wrapper.appendChild(element);

  return wrapper;
}

function loadJSONFromUser(callback) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json,application/json";

  input.onchange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        callback(data);
      } catch (err) {
        console.error("Invalid JSON file", err);
      }
    };

    reader.readAsText(file);
  };

  input.click();
}


loadJSONFromUser((j) => {
  data = j;
  refreshList();
});
function downloadJSON(filename = "profile.json") {
  const json = JSON.stringify(data, null, 2);

  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  URL.revokeObjectURL(url);
}