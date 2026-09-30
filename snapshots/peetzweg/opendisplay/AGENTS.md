# Local macOS development

Keep the development app identities stable. macOS TCC associates Screen
Recording and Accessibility grants with the bundle identifier and signing
requirement; changing either creates stale or duplicate permission entries.

- Sender Debug bundle ID: `com.peetzweg.opensidecar.mac.debug`
- Receiver Debug bundle ID: `com.peetzweg.opensidecar.mac.receiver.debug`
- Keep Debug builds separate from the release bundle IDs.
- Build the sender into `build/Build/Products/Debug/OpenDisplay Dev.app` and
  launch it with `./run.sh`. The script normalizes an ad hoc build's designated
  requirement before launch. Do not rebuild or re-sign it after granting Screen
  Recording during a test session.
- If the Debug sender's permission row is stale, quit it, run
  `tccutil reset ScreenCapture com.peetzweg.opensidecar.mac.debug`, launch the
  unchanged app, use its Grant button, and restart it once.

The Intel receiver test host is available as `ssh imac`. Deploy the x86_64
Debug receiver to `~/Applications/OpenDisplay Receiver Dev.app`; do not replace
the release receiver app. A windowed receiver is sufficient for protocol,
encode, and decode validation. Use its fullscreen video window for end-to-end
latency, presentation, scaling, and visual-quality measurements.
