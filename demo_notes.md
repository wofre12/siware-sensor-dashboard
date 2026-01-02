# Demo Script: Si-Ware Sensor Dashboard (2-5 Min)

## 1. Introduction (30s)
- **Goal**: Show a robust, multi-threaded industrial monitoring tool.
- **Key Highlight**: Decoupled architecture where 5 sensors are handled by 5 separate threads.

## 2. The Setup (30s)
- Show the `simulator/sensor_simulator.py` running in one terminal.
- Launch the app using `python -m app.main`.
- Point out that the system connects to each sensor independently.

## 3. Live Monitoring (1 min)
- **Table**: Show the live 2Hz updates. Explain the "OK" vs "Faulty Sensor" status.
- **Plots**: Point to the rolling 20-second history. Note how the "Vibration" sensor is deliberately noisy.
- **Responsiveness**: Resize the window or interact with the table to show the GUI remains smooth during data influx.

## 4. Alarm Scenario (1 min)
- Wait for a value to spike (Vibration or Temperature).
- **Point out**:
  1. The row turns **Red**.
  2. The Global Status changes to **ALARM**.
  3. A new entry appears in the **Alarm History** log.
  4. (If enabled) The **Desktop Notification** that just popped up.
- Explain the **de-duplication logic**: we don't spam logs; we only log the transition into an alarm state.

## 5. Remote Access (30s)
- Open a browser to `http://localhost:5000/api/status`.
- Show that the current state of the industrial floor is accessible via a REST API for integration with other systems.

## 6. Conclusion
- Summary: Clean, modular, and ready for production expansion.
