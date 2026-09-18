from pathlib import Path

p = Path("ios-app/SideBySideView.swift")
s = p.read_text()

# Every Side by Side install must propagate this patched iOS 27 build, not upstream v1.
s = s.replace(
    "https://github.com/FrizzleM/SideInstaller/releases/latest/download/SideInstaller.ipa",
    "https://github.com/someoneeelse/sideinstaller-Dani-/releases/download/ios27-beta/SideInstaller.ipa",
)

old = '''            // iOS drops the idle tunnel during sign-in and signing, and
            // `isConnected` doesn't detect it, so reconnect first.
            self.engine.log("Refreshing the link to \\(ip) before installing …")
            try self.connection.connect(deviceIP: ip, pairingFilePath: record)
            guard self.connection.isConnected else {
                throw EngineError.message(L("The link to their iPhone dropped — start again."))
            }
            self.engine.log("Installing the signed bundle via AFC + installation_proxy …")
            try self.connection.installSignedApp(bundlePath: bundle)
            self.engine.log("Install request completed.")'''

new = '''            // iOS 27 may drop the Wi-Fi tunnel during a large AFC upload.
            // Recover automatically instead of forcing the whole wizard to restart.
            var lastInstallError: Error?
            for attempt in 1...3 {
                do {
                    self.engine.log("Install attempt \\(attempt)/3: refreshing the link to \\(ip) …")
                    self.connection.disconnect()
                    try self.connection.connect(deviceIP: ip, pairingFilePath: record)
                    guard self.connection.isConnected else {
                        throw EngineError.message(L("The link to their iPhone is not ready."))
                    }
                    self.engine.log("Installing the signed bundle via AFC + installation_proxy …")
                    try self.connection.installSignedApp(bundlePath: bundle)
                    self.engine.log("Install request completed on attempt \\(attempt).")
                    lastInstallError = nil
                    break
                } catch {
                    lastInstallError = error
                    self.engine.log("Install attempt \\(attempt)/3 lost the link: \\(error)")
                    self.connection.disconnect()
                    if attempt < 3 { Thread.sleep(forTimeInterval: 0.8) }
                }
            }
            if let lastInstallError { throw lastInstallError }'''

if old not in s:
    raise SystemExit("Expected Side by Side install block not found")
s = s.replace(old, new)
p.write_text(s)
