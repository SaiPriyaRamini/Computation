import tkinter as tk
from tkinter import ttk
import math

# =========================
# 1. CONFIGURATION & DATA
# =========================

# --- Colors ---
PAL = {
    "bg": "#f4f5f7",
    "panel": "#ffffff",
    "panel_border": "#d1d5db",
    "text": "#1f2937",
    "muted": "#6b7280",
    "accent": "#6366f1",  # Indigo
    "ok": "#10b981",      # Emerald Green
    "err": "#ef4444",     # Red
    "canvas": "#ffffff",
    "node_fill": "#ffffff",
    "node_outline": "#000000",
    "row_even": "#ffffff",
    "row_odd": "#f9fafb",
}

# --- Machine Definitions ---

# DFA: Even number of 0s
DFA_STATES = ["A", "B"]
DFA_START  = "A"
DFA_ACCEPT = {"A"} 
DFA_TRANS  = {"A": {"0": "B", "1": "A"},
              "B": {"0": "A", "1": "B"}}

# NFA: Ends with 'ab'
NFA_STATES = ["A","B","C"]
NFA_START  = "A"
NFA_ACCEPT = {"C"}
NFA_TRANS  = {"A": {"a": {"A","B"}, "b": {"A"}},
              "B": {"b": {"C"}},
              "C": {}}

# NFA-Epsilon: (a|b)*abb
EPS = "ε"
NFAE_STATES = ["A","B","C","D","E"]
NFAE_START  = "A"
NFAE_ACCEPT = {"E"}
NFAE_TRANS  = {
    "A": {EPS: {"B"}},
    "B": {"a": {"B","C"}, "b": {"B"}},
    "C": {"b": {"D"}},
    "D": {"b": {"E"}},
    "E": {}
}

# PDA: a^n b^n
PDA_STATES = ["q_start","q_push","q_pop","q_accept"]
PDA_START  = "q_start"
PDA_ACCEPT = {"q_accept"}

# TM: a^n b^n c^n
TM_STATES = ["q0","q1","q2","q3","q4","qf"]
TM_START  = "q0"
TM_ACCEPT = {"qf"}
TM_TRANS_LOGIC = {
    ("q0", "a"): ("q1", "X", "R"),
    ("q0", "Y"): ("q4", "Y", "R"),
    ("q1", "a"): ("q1", "a", "R"),
    ("q1", "Y"): ("q1", "Y", "R"),
    ("q1", "b"): ("q2", "Y", "R"),
    ("q2", "b"): ("q2", "b", "R"),
    ("q2", "Z"): ("q2", "Z", "R"),
    ("q2", "c"): ("q3", "Z", "L"),
    ("q3", "a"): ("q3", "a", "L"),
    ("q3", "b"): ("q3", "b", "L"),
    ("q3", "Y"): ("q3", "Y", "L"),
    ("q3", "Z"): ("q3", "Z", "L"),
    ("q3", "X"): ("q0", "X", "R"),
    ("q4", "Y"): ("q4", "Y", "R"),
    ("q4", "Z"): ("q4", "Z", "R"),
    ("q4", "_"): ("qf", "_", "L"),
}

# =========================
# 2. LOGIC ENGINES
# =========================

def dfa_run(s: str):
    st = DFA_START; zeros = 0; trace=[f"start: {st}"]; path=[st]
    for i,ch in enumerate(s,1):
        if ch not in "01":
            trace.append("invalid symbol (alphabet {0,1}) → REJECT")
            return False, trace, path, zeros
        if ch=="0": zeros += 1
        nxt = DFA_TRANS[st][ch]
        trace.append(f"step {i}: read {ch}, {st} → {nxt}")
        st = nxt; path.append(st)
    ok = st in DFA_ACCEPT
    trace.append(f"final: {st} (zeros={zeros}) → {'ACCEPT' if ok else 'REJECT'}")
    return ok, trace, path, zeros

def nfa_run(s: str):
    active={NFA_START}; steps=[active.copy()]; trace=[f"start: {sorted(active)}"]
    for i,ch in enumerate(s,1):
        if ch not in "ab":
            trace.append("invalid symbol (alphabet {a,b}) → REJECT"); return False, trace, steps
        nxt=set()
        for q in active: nxt |= NFA_TRANS.get(q,{}).get(ch,set())
        active=nxt; steps.append(active.copy())
        trace.append(f"step {i}: read {ch} → {sorted(active)}")
    ok = bool(active & NFA_ACCEPT)
    trace.append(f"final: {sorted(active)} → {'ACCEPT' if ok else 'REJECT'}")
    return ok, trace, steps

def nfae_eclose(S:set[str]):
    stack=list(S); seen=set(S)
    while stack:
        q=stack.pop()
        for nq in NFAE_TRANS.get(q,{}).get(EPS,set()):
            if nq not in seen: seen.add(nq); stack.append(nq)
    return seen

def nfae_run(s:str):
    active = nfae_eclose({NFAE_START}); steps=[active.copy()]
    trace=[f"start ε-closure: {sorted(active)}"]
    for i,ch in enumerate(s,1):
        if ch not in "ab":
            trace.append("invalid symbol (alphabet {a,b}) → REJECT"); return False, trace, steps
        move=set()
        for q in active: move |= NFAE_TRANS.get(q,{}).get(ch,set())
        active = nfae_eclose(move); steps.append(active.copy())
        trace.append(f"step {i}: read {ch} → move {sorted(move)} → ε-closure {sorted(active)}")
    ok = bool(active & NFAE_ACCEPT)
    trace.append(f"final ε-closure: {sorted(active)} → {'ACCEPT' if ok else 'REJECT'}")
    return ok, trace, steps

def pda_run(s:str):
    trace=["start: q_start"]; stack=[]; phase="push"
    if s=="": trace.append("ε input, stack empty → q_accept → ACCEPT"); return True, trace
    for i,ch in enumerate(s,1):
        if ch not in "ab": trace.append(f"invalid '{ch}' → REJECT"); return False, trace
        if ch=="a" and phase=="push":
            stack.append("A"); trace.append(f"step {i}: read a, push A → stack={len(stack)}")
        elif ch=="b":
            if phase=="push": phase="pop"; trace.append(f"step {i}: first b → switch to pop phase")
            if not stack: trace.append(f"step {i}: pop on empty stack → REJECT"); return False, trace
            stack.pop(); trace.append(f"step {i}: read b, pop A → stack={len(stack)}")
        else:
            trace.append(f"step {i}: saw a after b-phase → REJECT"); return False, trace
    ok = (len(stack)==0)
    trace.append("end: stack empty → q_accept → ACCEPT" if ok else "end: stack not empty → REJECT")
    return ok, trace

def tm_run_logic(s: str):
    tape = list(s)
    if not tape: tape = ["_"] 
    head = 0; state = TM_START
    trace = [f"Start: {state}, Tape: {''.join(tape)}"]
    
    step_count = 0; MAX_STEPS = 1000
    
    while step_count < MAX_STEPS:
        if head < 0: tape.insert(0, "_"); head = 0
        elif head >= len(tape): tape.append("_")
        
        curr_char = tape[head]
        key = (state, curr_char)
        if key not in TM_TRANS_LOGIC:
            trace.append(f"Step {step_count}: No transition for ({state}, {curr_char}) → HALT/REJECT")
            return False, trace
            
        next_st, write_ch, direction = TM_TRANS_LOGIC[key]
        tape[head] = write_ch
        state = next_st
        
        trace.append(f"Step {step_count}: {state}, Tape: {''.join(tape).replace('_', 'B')}")
        
        if direction == "R": head += 1
        elif direction == "L": head -= 1
        step_count += 1
        
        if state in TM_ACCEPT:
            trace.append("State is qf → ACCEPT")
            return True, trace

    trace.append("Max steps reached → REJECT")
    return False, trace

# =========================
# 3. GUI APPLICATION
# =========================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automata Playground")
        self.geometry("1300x900")
        
        self.method = tk.StringVar(value="DFA (even 0s)")
        self.input_str = tk.StringVar()
        self._R = 35  

        # Logic State
        self._dfa_last_final=None; self._dfa_last_ok=None
        self._nfa_last_set=set(); self._nfa_last_ok=None
        self._nfae_last_set=set(); self._nfae_last_ok=None
        self._pda_last_ok=None; self._tm_last_ok=None
        
        # Canvas Management
        self.main_canvas = None
        self.popup_window = None
        self.popup_canvas = None

        self._style()
        self._build_top()
        self._build_body()
        self._load_method()

    def _style(self):
        self.configure(bg=PAL["bg"])
        s = ttk.Style(); s.theme_use("default")
        s.configure("TFrame", background=PAL["bg"])
        s.configure("TLabel", background=PAL["bg"], foreground=PAL["text"])
        s.configure("Header.TLabel", background=PAL["bg"], foreground=PAL["text"], font=("Segoe UI", 12, "bold"))
        s.configure("Accent.TButton", background=PAL["accent"], foreground="#ffffff")
        s.configure("Treeview", background=PAL["row_even"], fieldbackground=PAL["row_even"], 
                    foreground=PAL["text"], bordercolor=PAL["panel_border"], rowheight=25)

    def _build_top(self):
        bar = ttk.Frame(self, padding=(15,15))
        bar.pack(side=tk.TOP, fill=tk.X)
        
        row = ttk.Frame(bar)
        row.pack(fill=tk.X)

        ttk.Label(row, text="Machine Type:").pack(side=tk.LEFT, padx=(0,10))
        cb = ttk.Combobox(row, textvariable=self.method, 
                          values=["DFA (even 0s)","NFA (ends with 'ab')","NFAε ((a|b)*abb)","PDA (a^n b^n)","TM (a^n b^n c^n)"],
                          state="readonly", width=25)
        cb.pack(side=tk.LEFT)
        cb.bind("<<ComboboxSelected>>", lambda e: self._load_method())

        ttk.Label(row, text="Input String:").pack(side=tk.LEFT, padx=(20,10))
        ttk.Entry(row, textvariable=self.input_str, width=20).pack(side=tk.LEFT)

        ttk.Button(row, text="Run Simulation", command=self.on_run, style="Accent.TButton").pack(side=tk.LEFT, padx=(10,0))
        ttk.Button(row, text="Reset", command=self.on_clear).pack(side=tk.LEFT, padx=(5,0))

        self.result_lbl = ttk.Label(row, text="Waiting...", font=("Segoe UI", 12, "bold"), foreground=PAL["muted"])
        self.result_lbl.pack(side=tk.LEFT, padx=(25,0))

        self.meta = ttk.Label(bar, text="", foreground=PAL["muted"], font=("Segoe UI", 9))
        self.meta.pack(anchor="w", pady=(5,0))

    def _build_body(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))

        # Left Pane
        left = ttk.Frame(main, width=400)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0,15))
        
        ttk.Label(left, text="Transitions", style="Header.TLabel").pack(anchor="w", pady=(0,5))
        self.tree = ttk.Treeview(left, columns=(), show="headings", height=8)
        self.tree.pack(fill=tk.X)

        ttk.Label(left, text="Execution Trace", style="Header.TLabel").pack(anchor="w", pady=(15,5))
        self.trace = tk.Text(left, height=20, width=50, wrap="none", 
                             bg=PAL["panel"], fg=PAL["text"], 
                             font=("Consolas", 10), relief="flat", borderwidth=1)
        self.trace.pack(fill=tk.BOTH, expand=True)

        # Right Pane (Visuals)
        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header with Maximize button
        vhead = ttk.Frame(right)
        vhead.pack(fill=tk.X, pady=(0,5))
        ttk.Label(vhead, text="Visual Diagram", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Button(vhead, text="🔍 Maximize Diagram", command=self._toggle_maximize).pack(side=tk.RIGHT)
        
        self.main_canvas = tk.Canvas(right, bg=PAL["canvas"], highlightthickness=1, highlightbackground=PAL["panel_border"])
        self.main_canvas.pack(fill=tk.BOTH, expand=True)
        self.main_canvas.bind("<Configure>", lambda e: self._redraw_single(self.main_canvas))

        self.samples = {
            "DFA (even 0s)": ["0010","010","1100"],
            "NFA (ends with 'ab')": ["babab","baa","ab"],
            "NFAε ((a|b)*abb)": ["abb","aabb","bababb"],
            "PDA (a^n b^n)": ["aaabbb","aab","ab"],
            "TM (a^n b^n c^n)": ["aaabbbccc","aabbcc","abc"],
        }

    def _toggle_maximize(self):
        if self.popup_window is not None and tk.Toplevel.winfo_exists(self.popup_window):
            self.popup_window.lift()
            return

        self.popup_window = tk.Toplevel(self)
        self.popup_window.title("Visual State Diagram - Full View")
        self.popup_window.geometry("1000x700")
        self.popup_window.configure(bg=PAL["bg"])
        
        self.popup_canvas = tk.Canvas(self.popup_window, bg=PAL["canvas"], highlightthickness=0)
        self.popup_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.popup_window.bind("<Configure>", lambda e: self._redraw_single(self.popup_canvas))
        self._redraw_all()

    # ==========================================
    # 4. DRAWING PRIMITIVES (Multi-Canvas Safe)
    # ==========================================
    
    def _node_core(self, cv, x, y, name, kind, accept=False, start=False):
        r = self._R
        if start:
            cv.create_line(x - r - 40, y, x - r, y, width=2, arrow=tk.LAST, arrowshape=(10, 12, 5), fill=PAL["node_outline"])
            cv.create_text(x - r - 55, y, text="Start", font=("Segoe UI", 10))

        cv.create_oval(x - r, y - r, x + r, y + r, outline=PAL["node_outline"], width=2, fill=PAL["node_fill"], tags=("node",))
        if accept:
            cv.create_oval(x - r + 5, y - r + 5, x + r - 5, y + r - 5, outline=PAL["node_outline"], width=1.5, tags=("node",))
        cv.create_text(x, y, text=name, font=("Times New Roman", 12, "bold"), fill=PAL["text"], tags=("node_text",))

    def _halo(self, cv, x, y, color):
        r = self._R
        cv.create_oval(x - r - 6, y - r - 6, x + r + 6, y + r + 6, outline=color, width=4, tags=("halo",))

    def _edge(self, cv, p_src, p_dst, label, curve=0, label_offset_correction=0):
        """
        curve: +ve curves 'right' relative to direction, -ve curves 'left'.
        label_offset_correction: Adjusts label distance from line (useful for deep loops).
        """
        r = self._R; x1, y1 = p_src; x2, y2 = p_dst
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0: return 
        
        ux, uy = dx/dist, dy/dist
        sx, sy = x1 + ux * r, y1 + uy * r
        ex, ey = x2 - ux * r, y2 - uy * r
        mx, my = (sx + ex)/2, (sy + ey)/2
        px, py = -uy, ux
        
        cx, cy = mx + px * curve, my + py * curve
        
        cv.create_line(sx, sy, cx, cy, ex, ey, smooth=True, splinesteps=32, width=1.5, arrow=tk.LAST, arrowshape=(10, 12, 5), fill=PAL["node_outline"], tags=("edge",))
        
        # Label Positioning
        base_offset = 20
        if curve < 0: base_offset = -20 
        elif curve == 0: base_offset = -20 # Default straight text above
        
        # Add extra correction (e.g. to push text further down on a deep bottom curve)
        total_offset = curve + base_offset + label_offset_correction
        if curve == 0: total_offset = base_offset

        lx, ly = mx + px * total_offset, my + py * total_offset
        
        t_id = cv.create_text(lx, ly, text=label, font=("Consolas", 9), fill=PAL["text"], tags=("edge_label",))
        bbox = cv.bbox(t_id)
        if bbox:
            bg_id = cv.create_rectangle(bbox[0]-3, bbox[1]-1, bbox[2]+3, bbox[3]+1, fill=PAL["canvas"], outline="", tags=("edge_label_bg",))
            cv.tag_lower(bg_id, t_id)

    def _loop(self, cv, center, label, loc="top"):
        r = self._R; x, y = center; loop_h = 55
        if loc == "top":
            cv.create_line(x - 15, y - r + 2, x - 25, y - r - loop_h, x + 25, y - r - loop_h, x + 15, y - r + 2, smooth=True, splinesteps=32, width=1.5, arrow=tk.LAST, arrowshape=(10, 12, 5), tags=("edge",))
            t_y = y - r - loop_h - 10
            t_id = cv.create_text(x, t_y, text=label, font=("Consolas", 9), fill=PAL["text"], tags=("edge_label",))
        elif loc == "left":
            cv.create_line(x - r + 2, y + 15, x - r - loop_h, y + 25, x - r - loop_h, y - 25, x - r + 2, y - 15, smooth=True, splinesteps=32, width=1.5, arrow=tk.LAST, arrowshape=(10, 12, 5), tags=("edge",))
            t_x = x - r - loop_h - 10
            t_id = cv.create_text(t_x, y, text=label, font=("Consolas", 9), fill=PAL["text"], tags=("edge_label",))
        
        bbox = cv.bbox(t_id)
        if bbox:
            bg_id = cv.create_rectangle(bbox[0]-3, bbox[1]-1, bbox[2]+3, bbox[3]+1, fill=PAL["canvas"], outline="", tags=("edge_label_bg",))
            cv.tag_lower(bg_id, t_id)

    # =========================
    # 5. MACHINE VISUALIZERS
    # =========================

    def _draw_dfa(self, cv):
        W = cv.winfo_width(); H = cv.winfo_height()
        cy = H / 2; cx = W / 2; spacing = 200
        pA = (cx - spacing/2, cy); pB = (cx + spacing/2, cy)
        
        self._edge(cv, pA, pB, "0", 40)
        self._edge(cv, pB, pA, "0", 40)
        self._loop(cv, pA, "1")
        self._loop(cv, pB, "1")
        
        self._node_core(cv, *pA, "A", "DFA", start=True, accept=True) 
        self._node_core(cv, *pB, "B", "DFA", accept=False)
        
        if self._dfa_last_final:
            target = pA if self._dfa_last_final == "A" else pB
            self._halo(cv, *target, PAL["ok"] if self._dfa_last_ok else PAL["err"])

    def _draw_nfa(self, cv):
        W = cv.winfo_width(); H = cv.winfo_height()
        cy = H / 2; spacing = 180
        pA = (W/2 - spacing, cy); pB = (W/2, cy); pC = (W/2 + spacing, cy)
        
        self._loop(cv, pA, "a, b")
        self._edge(cv, pA, pB, "a", 0)
        self._edge(cv, pB, pC, "b", 0)
        
        self._node_core(cv, *pA, "A", "NFA", start=True)
        self._node_core(cv, *pB, "B", "NFA")
        self._node_core(cv, *pC, "C", "NFA", accept=True)
        
        if self._nfa_last_set and self._nfa_last_ok is not None:
            active = self._nfa_last_set; is_success = self._nfa_last_ok
            mapping = {"A":pA, "B":pB, "C":pC}
            for state_name in active:
                if state_name not in mapping: continue
                if is_success:
                    if state_name in NFA_ACCEPT: self._halo(cv, *mapping[state_name], PAL["ok"])
                else:
                    self._halo(cv, *mapping[state_name], PAL["err"])

    def _draw_nfae(self, cv):
        W = cv.winfo_width(); H = cv.winfo_height()
        cy = H / 2; spacing = 130
        total_width = 4 * spacing; start_x = (W - total_width) / 2
        
        pA = (start_x, cy); pB = (start_x + spacing, cy); pC = (start_x + spacing*2, cy)
        pD = (start_x + spacing*3, cy); pE = (start_x + spacing*4, cy)
        
        self._edge(cv, pA, pB, EPS, 0)
        self._loop(cv, pB, "a, b")
        self._edge(cv, pB, pC, "a", 0)
        self._edge(cv, pC, pD, "b", 0)
        self._edge(cv, pD, pE, "b", 0)

        self._node_core(cv, *pA, "A", "NFAE", start=True)
        self._node_core(cv, *pB, "B", "NFAE")
        self._node_core(cv, *pC, "C", "NFAE")
        self._node_core(cv, *pD, "D", "NFAE")
        self._node_core(cv, *pE, "E", "NFAE", accept=True)
        
        if self._nfae_last_set and self._nfae_last_ok is not None:
            active = self._nfae_last_set; is_success = self._nfae_last_ok
            mapping = {"A":pA, "B":pB, "C":pC, "D":pD, "E":pE}
            for state_name in active:
                if state_name not in mapping: continue
                if is_success:
                    if state_name in NFAE_ACCEPT: self._halo(cv, *mapping[state_name], PAL["ok"])
                else:
                    self._halo(cv, *mapping[state_name], PAL["err"])

    def _draw_pda(self, cv):
        W = cv.winfo_width(); H = cv.winfo_height()
        cy = H / 2; spacing = 180
        pStart = (W/2 - spacing*1.5, cy); pPush = (W/2 - spacing*0.5, cy)
        pPop = (W/2 + spacing*0.5, cy); pAcc = (W/2 + spacing*1.5, cy)
        
        self._edge(cv, pStart, pPush, f"ε, ε -> {EPS}", 0)
        self._loop(cv, pPush, "a, ε -> A")
        self._edge(cv, pPush, pPop, "b, A -> ε", 0)
        self._loop(cv, pPop, "b, A -> ε")
        self._edge(cv, pPop, pAcc, "ε, Z -> ε", 0)
        
        self._node_core(cv, *pStart, "start", "PDA", start=True)
        self._node_core(cv, *pPush, "push", "PDA")
        self._node_core(cv, *pPop, "pop", "PDA")
        self._node_core(cv, *pAcc, "acc", "PDA", accept=True)
        
        if self._pda_last_ok is not None:
            self._halo(cv, *pAcc, PAL["ok"] if self._pda_last_ok else PAL["err"])

    def _draw_tm(self, cv):
        W = cv.winfo_width(); H = cv.winfo_height()
        
        # Increased vertical spacing to allow the "under" swoop
        spacing = 160
        row1_y = H/2 - 100 
        row2_y = H/2 + 120 
        start_x = W/2 - spacing * 1.5
        
        p0 = (start_x, row1_y); p1 = (start_x + spacing, row1_y)
        p2 = (start_x + spacing*2, row1_y); p3 = (start_x + spacing*3, row1_y)
        p4 = (start_x, row2_y); pf = (start_x + spacing, row2_y)
        
        # Standard Edges
        self._edge(cv, p0, p1, "(a,X,R)", 0)
        self._edge(cv, p0, p4, "(Y,Y,R)", 20) 
        self._loop(cv, p1, "(Y,Y,R)\n(a,a,R)", "top")
        self._edge(cv, p1, p2, "(b,Y,R)", 0)
        self._loop(cv, p2, "(Z,Z,R)\n(b,b,R)", "top")
        self._edge(cv, p2, p3, "(c,Z,L)", 0)
        self._loop(cv, p3, "(a,a,L)\n(Y,Y,L)\n(b,b,L)\n(Z,Z,L)", "top")
        
        # SPECIAL SWOOP: q3 -> q0 (Under)
        # Curve smaller magnitude and correction to keep label close to the curve
        self._edge(cv, p3, p0, "(X,X,R)", curve=-100, label_offset_correction=50)
        
        self._loop(cv, p4, "(Y,Y,R)\n(Z,Z,R)", "left")
        self._edge(cv, p4, pf, "(B,B,L)", 0)
        
        self._node_core(cv, *p0, "q0", "TM", start=True)
        self._node_core(cv, *p1, "q1", "TM")
        self._node_core(cv, *p2, "q2", "TM")
        self._node_core(cv, *p3, "q3", "TM")
        self._node_core(cv, *p4, "q4", "TM")
        self._node_core(cv, *pf, "qf", "TM", accept=True)
        
        if self._tm_last_ok is not None:
            self._halo(cv, *pf, PAL["ok"] if self._tm_last_ok else PAL["err"])

    # =========================
    # 6. CONTROLLER LOGIC
    # =========================

    def _load_method(self):
        m = self.method.get()
        self.result_lbl.config(text="Waiting...", foreground=PAL["muted"])
        self.trace.delete("1.0", tk.END)
        self.input_str.set(self.samples[m][0])

        if m.startswith("DFA"):
            cols=("State","on 0","on 1")
            self._setup_tree(cols)
            rows=[(q,DFA_TRANS[q]["0"],DFA_TRANS[q]["1"]) for q in DFA_STATES]
            self._fill_tree(rows)
            self.meta.config(text="DFA: Accept even # of 0s.")
        elif "NFAε" in m:
            cols=("State","on a","on b","on ε")
            self._setup_tree(cols)
            def fmt(S): return "{" + ",".join(sorted(S)) + "}" if S else "∅"
            rows=[]
            for q in NFAE_STATES:
                row=NFAE_TRANS.get(q,{})
                rows.append((q, fmt(row.get("a",set())), fmt(row.get("b",set())), fmt(row.get(EPS,set()))))
            self._fill_tree(rows)
            self.meta.config(text="NFA-ε: Pattern (a|b)*abb.")
        elif m.startswith("NFA"):
            cols=("State","on a","on b")
            self._setup_tree(cols)
            def fmt(S): return "{" + ",".join(sorted(S)) + "}" if S else "∅"
            rows=[]
            for q in NFA_STATES:
                row=NFA_TRANS.get(q,{})
                rows.append((q, fmt(row.get("a",set())), fmt(row.get("b",set()))))
            self._fill_tree(rows)
            self.meta.config(text="NFA: Ends with 'ab'.")
        elif m.startswith("PDA"):
            cols=("From","Input/Stack Action","To")
            self._setup_tree(cols)
            rows=[
                ("q_start","ε → go push mode","q_push"),
                ("q_push","read a, push A","q_push"),
                ("q_push","read b, pop A","q_pop"),
                ("q_pop", "read b, pop A","q_pop"),
                ("q_pop", "stack empty & ε","q_accept"),
            ]
            self._fill_tree(rows)
            self.meta.config(text="PDA: a^n b^n.")
        else:
            cols=("State", "Char", "Next", "Write", "Dir")
            self._setup_tree(cols)
            rows = []
            for (st, ch), (nst, w, d) in TM_TRANS_LOGIC.items():
                rows.append((st, ch, nst, w, d))
            self._fill_tree(rows)
            self.meta.config(text="TM: a^n b^n c^n.")

        self._clear_state()
        self._redraw_all()

    def _setup_tree(self, cols):
        self.tree.config(columns=cols)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=tk.CENTER, width=80)

    def _fill_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            tag = "even" if i%2==0 else "odd"
            self.tree.insert("", tk.END, values=row, tags=(tag,))
        self.tree.tag_configure("even", background=PAL["row_even"])
        self.tree.tag_configure("odd", background=PAL["row_odd"])

    def _clear_state(self):
        self._dfa_last_final=None; self._dfa_last_ok=None
        self._nfa_last_set=set(); self._nfa_last_ok=None
        self._nfae_last_set=set(); self._nfae_last_ok=None
        self._pda_last_ok=None; self._tm_last_ok=None

    def on_clear(self):
        self.input_str.set("")
        self.trace.delete("1.0", tk.END)
        self.result_lbl.config(text="Waiting...", foreground=PAL["muted"])
        self._clear_state()
        self._redraw_all()

    def on_run(self):
        s = self.input_str.get().strip()
        m = self.method.get()
        self._clear_state()

        if m.startswith("DFA"):
            ok,trace,path,_ = dfa_run(s)
            self._display_result(ok, trace)
            self._dfa_last_final = path[-1]
            self._dfa_last_ok = ok

        elif "NFAε" in m:
            ok,trace,steps = nfae_run(s)
            self._display_result(ok, trace)
            self._nfae_last_set = steps[-1]
            self._nfae_last_ok = ok

        elif m.startswith("NFA"):
            ok,trace,steps = nfa_run(s)
            self._display_result(ok, trace)
            self._nfa_last_set = steps[-1]
            self._nfa_last_ok = ok

        elif m.startswith("PDA"):
            ok,trace = pda_run(s)
            self._display_result(ok, trace)
            self._pda_last_ok = ok

        elif m.startswith("TM"):
            ok,trace = tm_run_logic(s)
            self._display_result(ok, trace)
            self._tm_last_ok = ok
        
        self._redraw_all()

    def _display_result(self, ok, trace):
        txt = "ACCEPTED" if ok else "REJECTED"
        col = PAL["ok"] if ok else PAL["err"]
        self.result_lbl.config(text=txt, foreground=col)
        self.trace.delete("1.0", tk.END)
        self.trace.insert(tk.END, "\n".join(trace))
    
    def _redraw_all(self):
        # Redraw main canvas
        self._redraw_single(self.main_canvas)
        # Redraw popup canvas if open
        if self.popup_window is not None and tk.Toplevel.winfo_exists(self.popup_window):
            self._redraw_single(self.popup_canvas)

    def _redraw_single(self, cv):
        cv.delete("all")
        m = self.method.get()
        if m.startswith("DFA"): self._draw_dfa(cv)
        elif "NFAε" in m: self._draw_nfae(cv)
        elif m.startswith("NFA"): self._draw_nfa(cv)
        elif m.startswith("PDA"): self._draw_pda(cv)
        else: self._draw_tm(cv)

if __name__ == "__main__":
    App().mainloop()