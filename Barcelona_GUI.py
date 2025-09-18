import os
import csv
import tkinter as tk
import threading
import socket
from PIL import Image, ImageTk
from f1_2020_telemetry.packets import unpack_udp_packet

# ─────────────────────────────────────────────────────────────────────────────
# 1) Telemetry listener (background thread)
#    • Reads LAP_DATA to update shared['lap'], shared['lapDistance'], shared['totalDistance']
#    • Reads CAR_TELEMETRY to update shared fields + write a CSV row that now also includes
#      lapDistance and totalDistance on every telemetry line.
# ─────────────────────────────────────────────────────────────────────────────
def telemetry_listener(shared, csv_writer):
    UDP_IP   = "0.0.0.0"
    UDP_PORT = 20777
    LAP_DATA      = 2
    CAR_TELEMETRY = 6

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    # Keep track of the previous lapDistance, so we can detect crossing the line:
    prev_lap_distance = 0.0
    track_length_estimate = None  # we can approximate track length once.

    while True:
        raw, _ = sock.recvfrom(2048)
        packet = unpack_udp_packet(raw)
        pid    = packet.header.packetId
        idx    = packet.header.playerCarIndex

        # ── Process Lap Data ───────────────────────────────────────────────────
        if pid == LAP_DATA:
            lap = packet.lapData[idx]

            # current lap number
            shared['lap'] = lap.currentLapNum

            # distance around the current lap (meters)
            lap_distance = lap.lapDistance
            shared['lapDistance'] = lap_distance

            # total distance across the session (meters)
            total_distance = lap.totalDistance
            shared['totalDistance'] = total_distance

            # Estimate track length on the first lap:
            if shared['lap'] == 1 and track_length_estimate is None:
                # As soon as the game increments from 0→1 lap, lapDistance will jump from ~trackLength→small.
                if prev_lap_distance > lap_distance + 100:  # e.g. prev was ~5000m, new is ~50m
                    track_length_estimate = prev_lap_distance
                    shared['trackLength'] = track_length_estimate
            prev_lap_distance = lap_distance

        # ── Process Car Telemetry ─────────────────────────────────────────────
        elif pid == CAR_TELEMETRY:
            t = packet.carTelemetryData[idx]

            # Update shared for GUI
            shared['gear']     = t.gear
            shared['rpm']      = t.engineRPM
            shared['speed']    = t.speed
            shared['throttle'] = t.throttle * 100
            shared['brake']    = t.brake * 100
            shared['steer']    = t.steer * 100
            shared['clutch']   = t.clutch
            shared['drs']      = t.drs
            shared['revLightsPercent'] = t.revLightsPercent
            shared['brakesTemperature']      = list(t.brakesTemperature)
            shared['tyresSurfaceTemperature'] = list(t.tyresSurfaceTemperature)
            shared['tyresInnerTemperature']   = list(t.tyresInnerTemperature)
            shared['engineTemperature']       = t.engineTemperature
            shared['tyre_pressures']          = list(t.tyresPressure)
            shared['surfaceType']             = list(t.surfaceType)
            shared['buttonStatus']            = packet.buttonStatus
            shared['mfdPanelIndex']           = packet.mfdPanelIndex
            shared['mfdPanelIndexSecondaryPlayer'] = packet.mfdPanelIndexSecondaryPlayer
            shared['suggestedGear']           = packet.suggestedGear

            # Also grab the most recent lapDistance/totalDistance from shared:
            lap_distance   = shared.get('lapDistance', 0.0)
            total_distance = shared.get('totalDistance', 0.0)

            # Build CSV row: FrameID, SessionTime, Lap, LapDistance, TotalDistance, then all CarTelemetry
            row = [
                packet.header.frameIdentifier,
                f"{packet.header.sessionTime:.3f}",
                shared['lap'],
                f"{lap_distance:.3f}",
                f"{total_distance:.3f}",
                # CarTelemetryData scalar fields:
                t.speed,
                f"{t.throttle:.3f}",
                f"{t.steer:.3f}",
                f"{t.brake:.3f}",
                t.clutch,
                t.gear,
                t.engineRPM,
                t.drs,
                t.revLightsPercent,
                # brakesTemperature[4]
                *t.brakesTemperature,
                # tyresSurfaceTemperature[4]
                *t.tyresSurfaceTemperature,
                # tyresInnerTemperature[4]
                *t.tyresInnerTemperature,
                # engineTemperature
                t.engineTemperature,
                # tyresPressure[4]
                *t.tyresPressure,
                # surfaceType[4]
                *t.surfaceType,
                # buttonStatus, mfdPanelIndex, mfdPanelIndexSecondaryPlayer, suggestedGear
                packet.buttonStatus,
                packet.mfdPanelIndex,
                packet.mfdPanelIndexSecondaryPlayer,
                packet.suggestedGear
            ]

            csv_writer.writerow(row)

# ─────────────────────────────────────────────────────────────────────────────
# 2) Main GUI + CSV logging
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # 2.1) Shared state dictionary (initialize all keys that update_gui expects)
    shared = {
        'lap':                         0,
        'lapDistance':                0.0,
        'totalDistance':              0.0,
        'trackLength':                None,
        'speed':                       0,
        'throttle':                  0.0,
        'steer':                     0.0,
        'brake':                     0.0,
        'clutch':                      0,
        'gear':                        0,
        'rpm':                         0,
        'drs':                         0,
        'revLightsPercent':            0,
        'brakesTemperature':       [0, 0, 0, 0],
        'tyresSurfaceTemperature':[0, 0, 0, 0],
        'tyresInnerTemperature':  [0, 0, 0, 0],
        'engineTemperature':           0,
        'tyre_pressures':          [0.0, 0.0, 0.0, 0.0],
        'surfaceType':             [0, 0, 0, 0],
        'buttonStatus':               0,
        'mfdPanelIndex':              0,
        'mfdPanelIndexSecondaryPlayer':0,
        'suggestedGear':              0,
        'sector':                     0
    }

    # 2.2) Open CSV file and write header (including LapDistance & TotalDistance)
    csv_file = open("f1_full_telemetry.csv", "w", newline="")
    writer = csv.writer(csv_file)

    header = [
        "FrameID",
        "SessionTime",
        "Lap",
        "LapDistance_m",
        "TotalDistance_m",
        # CarTelemetryData scalar fields:
        "Speed_kmh",
        "Throttle",
        "Steer",
        "Brake",
        "Clutch",
        "Gear",
        "EngineRPM",
        "DRS",
        "RevLightsPercent",
        # brakesTemperature[4]
        "BrakeTemp_FL", "BrakeTemp_FR", "BrakeTemp_RL", "BrakeTemp_RR",
        # tyresSurfaceTemperature[4]
        "TyreSurfTemp_FL", "TyreSurfTemp_FR", "TyreSurfTemp_RL", "TyreSurfTemp_RR",
        # tyresInnerTemperature[4]
        "TyreInnerTemp_FL", "TyreInnerTemp_FR", "TyreInnerTemp_RL", "TyreInnerTemp_RR",
        # engineTemperature
        "EngineTemperature",
        # tyresPressure[4]
        "TyrePressure_FL", "TyrePressure_FR", "TyrePressure_RL", "TyrePressure_RR",
        # surfaceType[4]
        "SurfaceType_FL", "SurfaceType_FR", "SurfaceType_RL", "SurfaceType_RR",
        # buttonStatus, mfdPanelIndex, mfdPanelIndexSecondaryPlayer, suggestedGear
        "ButtonStatus",
        "MFDPanelIndex",
        "MFDPanelIndexSecondaryPlayer",
        "SuggestedGear"
    ]
    writer.writerow(header)

    # 2.3) Start the telemetry_listener thread
    listener_thread = threading.Thread(
        target=telemetry_listener,
        args=(shared, writer),
        daemon=True
    )
    listener_thread.start()

    # ─────────────────────────────────────────────────────────────────────────
    # 2.4) Build the GUI window
    # ─────────────────────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("F1 2020 Telemetry Dashboard")
    root.configure(bg="black")
    root.geometry("900x600")
    root.resizable(False, False)

    root.columnconfigure(0, weight=0, minsize=320)
    root.columnconfigure(1, weight=1, minsize=580)
    root.rowconfigure(0, weight=1)

    # -- 2.4.1) LEFT FRAME: gear, bars, current corner, plus a display for lapDistance
    left_frame = tk.Frame(root, bg="black")
    left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

    # Gear display (row 0)
    gear_frame = tk.Frame(left_frame, bg="black", bd=2, relief="groove")
    gear_frame.grid(row=0, column=0, pady=(0, 10), sticky="w")
    gear_lbl = tk.Label(
        gear_frame,
        text="Gear: –",
        fg="white",
        bg="black",
        font=("Helvetica", 16, "bold"),
        width=10
    )
    gear_lbl.pack(padx=5, pady=5)

    # Lap Number + Distance (row 1)
    lapdist_frame = tk.Frame(left_frame, bg="black")
    lapdist_frame.grid(row=1, column=0, pady=(0, 15), sticky="w")
    lap_lbl = tk.Label(
        lapdist_frame,
        text="Lap: –",
        fg="white",
        bg="black",
        font=("Helvetica", 14)
    )
    lap_lbl.grid(row=0, column=0, padx=(0, 10))
    lapdist_lbl = tk.Label(
        lapdist_frame,
        text="Distance: 0.000 m",
        fg="white",
        bg="black",
        font=("Helvetica", 14)
    )
    lapdist_lbl.grid(row=0, column=1)

    # Bar graphs in order: RPM, Speed, Throttle, Brake (rows 2–5)
    bar_width_max = 200
    bar_height    = 20

    metrics = [
        ("RPM",      "#cc00cc"),
        ("Speed",    "#00aaff"),
        ("Throttle", "#00cc00"),
        ("Brake",    "#cc0000")
    ]

    bar_canvases = {}
    bar_rects    = {}
    value_labels = {}

    for i, (name, color) in enumerate(metrics, start=2):
        row_frame = tk.Frame(left_frame, bg="black")
        row_frame.grid(row=i, column=0, pady=5, sticky="w")

        # Name label
        name_lbl = tk.Label(
            row_frame,
            text=f"{name}:",
            fg="white",
            bg="black",
            font=("Helvetica", 12, "bold"),
            width=8,
            anchor="w"
        )
        name_lbl.grid(row=0, column=0, padx=(0, 5))

        # Canvas for bar background + colored rect
        canvas = tk.Canvas(
            row_frame,
            width=bar_width_max,
            height=bar_height,
            bg="#202020",
            highlightthickness=0
        )
        canvas.grid(row=0, column=1)
        canvas.create_rectangle(0, 0, bar_width_max, bar_height,
                                outline="#444444", width=1)
        rect_id = canvas.create_rectangle(0, 0, 0, bar_height,
                                          fill=color, width=0)

        # Numeric‐value label to the right
        val_lbl = tk.Label(
            row_frame,
            text="–",
            fg="white",
            bg="black",
            font=("Helvetica", 12),
            width=7,
            anchor="w"
        )
        val_lbl.grid(row=0, column=2, padx=(5, 0))

        bar_canvases[name] = canvas
        bar_rects[name]    = rect_id
        value_labels[name] = val_lbl

    # Current corner display (row 6)
    corner_frame = tk.Frame(left_frame, bg="black", bd=2, relief="ridge")
    corner_frame.grid(row=6, column=0, pady=(20, 0), sticky="w")
    corner_lbl = tk.Label(
        corner_frame,
        text="Corner: –",
        fg="white",
        bg="black",
        font=("Helvetica", 14),
        width=14
    )
    corner_lbl.pack(padx=5, pady=5)

    # ─────────────────────────────────────────────────────────────────────────
    # 2.5) RIGHT FRAME: tires + track
    # ─────────────────────────────────────────────────────────────────────────
    right_frame = tk.Frame(root, bg="black")
    right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    right_frame.rowconfigure(0, weight=0, minsize=260)
    right_frame.rowconfigure(1, weight=1, minsize=320)
    right_frame.columnconfigure(0, weight=1)

    # -- 2.5.1) Top-Right: Tire boxes (pressure + temperature)
    top_right = tk.Frame(right_frame, bg="black")
    top_right.grid(row=0, column=0, sticky="nw")

    TIRE_W        = 100
    TIRE_H        = 40
    TIRE_SPACING  = 20
    TEMP_SPACING  = 5
    LABEL_HEIGHT  = 20

    tire_canvas_width  = 2 * TIRE_W + TIRE_SPACING
    tire_canvas_height = 2 * (2 * TIRE_H + TEMP_SPACING + LABEL_HEIGHT) + TIRE_SPACING

    tire_canvas = tk.Canvas(
        top_right,
        width=tire_canvas_width,
        height=tire_canvas_height,
        bg="black",
        highlightthickness=0
    )
    tire_canvas.pack()

    pressure_rects = []
    pressure_texts = []
    temp_rects     = []
    temp_texts     = []

    corner_labels = ["FL", "FR", "RL", "RR"]

    for i in range(4):
        row = i // 2
        col = i % 2

        x0 = col * (TIRE_W + TIRE_SPACING)
        y0 = row * (2 * TIRE_H + TEMP_SPACING + LABEL_HEIGHT + TIRE_SPACING)

        # Pressure rectangle
        x1, y1 = x0 + TIRE_W, y0 + TIRE_H
        pr_id = tire_canvas.create_rectangle(
            x0, y0, x1, y1,
            outline="white", width=2,
            fill="#444444"
        )
        pressure_rects.append(pr_id)

        txt_id = tire_canvas.create_text(
            x0 + TIRE_W / 2,
            y0 + TIRE_H / 2,
            text="0.0 PSI",
            fill="white",
            font=("Helvetica", 10, "bold")
        )
        pressure_texts.append(txt_id)

        # Temperature rectangle below pressure
        y2, y3 = y1 + TEMP_SPACING, y1 + TEMP_SPACING + TIRE_H
        tr_id = tire_canvas.create_rectangle(
            x0, y2, x1, y3,
            outline="white", width=2,
            fill="#888888"
        )
        temp_rects.append(tr_id)

        tt_id = tire_canvas.create_text(
            x0 + TIRE_W / 2,
            y2 + TIRE_H / 2,
            text="0 °C",
            fill="white",
            font=("Helvetica", 10, "bold")
        )
        temp_texts.append(tt_id)

        # Corner label underneath
        tire_canvas.create_text(
            x0 + TIRE_W / 2,
            y3 + (LABEL_HEIGHT / 2),
            text=corner_labels[i],
            fill="white",
            font=("Helvetica", 10)
        )

    # -- 2.5.2) Bottom-Right: Track Image
    bottom_right = tk.Frame(right_frame, bg="black")
    bottom_right.grid(row=1, column=0, sticky="s")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    track_path = os.path.join(script_dir, "Barcelona_Circuit.png")

    try:
        track_img = Image.open(track_path)
        track_img = track_img.resize((550, 320), Image.LANCZOS)
        track_photo = ImageTk.PhotoImage(track_img)
        track_lbl = tk.Label(
            bottom_right,
            image=track_photo,
            bg="black"
        )
        track_lbl.image = track_photo
        track_lbl.pack()
    except Exception as e:
        print(f"Could not load track image at {track_path}: {e}")
        track_lbl = tk.Label(
            bottom_right,
            text="Track Image\nnot found",
            fg="white",
            bg="black",
            font=("Helvetica", 14),
            justify="center"
        )
        track_lbl.pack()

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: map [0°C..120°C] → heat map (light gray → red)
    # ─────────────────────────────────────────────────────────────────────────
    def temp_to_color(temp_c):
        t = max(min(temp_c / 120.0, 1.0), 0.0)
        base = 0xCC
        r = int(base + t * (0xFF - base))
        g = int(base - t * base)
        b = int(base - t * base)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ─────────────────────────────────────────────────────────────────────────
    # update_gui(): redraw every 10 ms instead of 100 ms
    # ─────────────────────────────────────────────────────────────────────────
    def update_gui():
        # A) Update Gear
        gear_lbl.config(text=f"Gear: {shared['gear']}")

        # B) Update Lap & LapDistance
        lap_lbl.config(text=f"Lap: {shared['lap']}")
        lapdist_lbl.config(text=f"Distance: {shared['lapDistance']:.3f} m")

        # C) Update bars + numeric values
        for name, color in metrics:
            if name == 'RPM':
                val = shared['rpm']
                pct = min(val / 15000.0, 1.0)
                new_w = pct * bar_width_max
                val_str = f"{val} RPM"
            elif name == 'Speed':
                val = shared['speed']
                pct = min(val / 300.0, 1.0)
                new_w = pct * bar_width_max
                val_str = f"{val} km/h"
            elif name == 'Throttle':
                val = shared['throttle']
                pct = min(val / 100.0, 1.0)
                new_w = pct * bar_width_max
                val_str = f"{val:.0f}%"
            else:  # 'Brake'
                val = shared['brake']
                pct = min(val / 100.0, 1.0)
                new_w = pct * bar_width_max
                val_str = f"{val:.0f}%"

            rect_id = bar_rects[name]
            canvas = bar_canvases[name]
            y0, y1 = canvas.coords(rect_id)[1], canvas.coords(rect_id)[3]
            canvas.coords(rect_id, 0, y0, new_w, y1)
            value_labels[name].config(text=val_str)

        # D) Update current corner (if desired)
        corner_lbl.config(text=f"Corner: {shared.get('sector', 0)}")

        # E) Update tire pressures + temperature color and numeric text
        for i in range(4):
            psi = shared['tyre_pressures'][i]
            temp_c = shared['tyresSurfaceTemperature'][i]  # show surface temp as heatmap

            tire_canvas.itemconfig(pressure_texts[i], text=f"{psi:.1f} PSI")
            tire_canvas.itemconfig(temp_rects[i], fill=temp_to_color(temp_c))
            tire_canvas.itemconfig(temp_texts[i], text=f"{temp_c} °C")

        # ←― Schedule next GUI update in 10 ms (0.01 s) instead of 100 ms
        root.after(10, update_gui)

    # Kick off the first GUI update after 10 ms
    root.after(10, update_gui)

    # ─────────────────────────────────────────────────────────────────────────
    # Close CSV on exit
    # ─────────────────────────────────────────────────────────────────────────
    def on_closing():
        csv_file.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
