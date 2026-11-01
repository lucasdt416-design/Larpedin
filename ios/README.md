# LarpedIn iOS app

A SwiftUI wrapper that shows https://larpedin-p1fd.onrender.com full screen in a WKWebView.

1. Open `ios/LarpedIn.xcodeproj` in Xcode, pick an iPhone simulator, and press Run (Cmd+R).
2. To run on your own iPhone, plug it in with a cable and unlock it.
3. Select the LarpedIn target > Signing & Capabilities, and choose your Apple ID under Team (a free Personal Team works).
4. If Xcode says the bundle id is taken, change `com.larpedin.app` to something unique.
5. Select your iPhone as the run destination at the top of Xcode, then press Run.
6. On the phone, open Settings > General > VPN & Device Management, tap your developer profile, and trust it.
7. With a free Personal Team, the build expires after 7 days. Press Run again to reinstall.

Command line build: `xcodebuild -project ios/LarpedIn.xcodeproj -scheme LarpedIn -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' CODE_SIGNING_ALLOWED=NO build`
