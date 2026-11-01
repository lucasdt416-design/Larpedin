import SwiftUI
import WebKit

let homeURL = URL(string: "https://larpedin-p1fd.onrender.com")!
let bg = Color(red: 0xF4 / 255, green: 0xF2 / 255, blue: 0xEE / 255)

@main
struct LarpedInApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}

struct ContentView: View {
    @State private var failed = false
    @State private var reloadToken = 0

    var body: some View {
        ZStack {
            bg.ignoresSafeArea()
            if failed {
                VStack(spacing: 20) {
                    Text("LarpedIn is warming up the hustle…")
                        .font(.title3.bold())
                        .multilineTextAlignment(.center)
                    Button("Retry") {
                        failed = false
                        reloadToken += 1
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(Color(red: 0x0A / 255, green: 0x66 / 255, blue: 0xC2 / 255))
                }
                .padding()
            } else {
                // .id forces a fresh web view on Retry.
                WebView(failed: $failed).id(reloadToken)
            }
        }
    }
}

struct WebView: UIViewRepresentable {
    @Binding var failed: Bool

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        config.applicationNameForUserAgent = "LarpedInApp/1.0"

        let web = WKWebView(frame: .zero, configuration: config)
        web.allowsBackForwardNavigationGestures = true
        web.navigationDelegate = context.coordinator
        web.uiDelegate = context.coordinator
        web.isOpaque = false
        web.backgroundColor = UIColor(bg)
        web.scrollView.backgroundColor = UIColor(bg)

        let refresh = UIRefreshControl()
        refresh.addTarget(context.coordinator, action: #selector(Coordinator.refresh(_:)), for: .valueChanged)
        web.scrollView.refreshControl = refresh

        web.load(URLRequest(url: homeURL))
        return web
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate {
        let parent: WebView
        init(_ parent: WebView) { self.parent = parent }

        @objc func refresh(_ sender: UIRefreshControl) {
            (sender.superview?.superview as? WKWebView)?.reload()
        }

        private func endRefresh(_ web: WKWebView) { web.scrollView.refreshControl?.endRefreshing() }

        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = action.request.url, let scheme = url.scheme?.lowercased() else {
                return decisionHandler(.allow)
            }
            if scheme != "http" && scheme != "https" {
                // mailto:, tel:, sms:, etc.
                if scheme != "about" && scheme != "blob" && scheme != "data" {
                    UIApplication.shared.open(url)
                    return decisionHandler(.cancel)
                }
                return decisionHandler(.allow)
            }
            let host = url.host?.lowercased() ?? ""
            let isOwn = host == homeURL.host
            let isOAuth = (host == "linkedin.com" || host.hasSuffix(".linkedin.com")) && url.path.hasPrefix("/oauth")
            // Only redirect top-level navigations; let iframes/subresources load.
            if action.targetFrame?.isMainFrame != false && !isOwn && !isOAuth {
                UIApplication.shared.open(url)
                return decisionHandler(.cancel)
            }
            decisionHandler(.allow)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) { endRefresh(webView) }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            endRefresh(webView); handle(error)
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            endRefresh(webView); handle(error)
        }

        private func handle(_ error: Error) {
            let e = error as NSError
            // Cancelled loads (e.g. we redirected to Safari) are not failures.
            if e.domain == NSURLErrorDomain && e.code == NSURLErrorCancelled { return }
            if e.domain == "WebKitErrorDomain" && e.code == 102 { return } // frame load interrupted
            parent.failed = true
        }

        // window.open -> load in the same web view.
        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                     for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            if let url = action.request.url { webView.load(URLRequest(url: url)) }
            return nil
        }
    }
}
