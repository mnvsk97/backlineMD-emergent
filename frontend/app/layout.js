import Providers from '@/components/Providers';
import './styles/globals.css';

export const metadata = {
  title: 'Emergent | Fullstack App',
  description: 'A product of emergent.sh',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <script src="https://assets.emergent.sh/scripts/emergent-main.js"></script>
        <script src="https://unpkg.com/rrweb@latest/dist/rrweb.min.js"></script>
        <script src="https://d2adkz2s9zrlge.cloudfront.net/rrweb-recorder-20250919-1.js"></script>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if (window.self !== window.top && '${process.env.NEXT_PUBLIC_ENABLE_VISUAL_EDITS}' === 'true') {
                var debugScript = document.createElement('script');
                debugScript.src = 'https://assets.emergent.sh/scripts/debug-monitor.js';
                document.head.appendChild(debugScript);
                window.tailwind = window.tailwind || {};
                tailwind.config = { corePlugins: { preflight: false } };
                var tailwindScript = document.createElement('script');
                tailwindScript.src = 'https://cdn.tailwindcss.com';
                document.head.appendChild(tailwindScript);
              }
            `,
          }}
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              !(function (t, e) {
                var o, n, p, r;
                e.__SV ||
                  ((window.posthog = e),
                  (e._i = []),
                  (e.init = function (i, s, a) {
                    function g(t, e) {
                      var o = e.split(".");
                      2 == o.length && ((t = t[o[0]]), (e = o[1])),
                        (t[e] = function () {
                          t.push(
                            [e].concat(
                              Array.prototype.slice.call(
                                arguments,
                                0,
                              ),
                            ),
                          );
                        });
                    }
                    ((p = t.createElement("script")).type =
                      "text/javascript"),
                      (p.crossOrigin = "anonymous"),
                      (p.async = !0),
                      (p.src =
                        s.api_host.replace(
                          ".i.posthog.com",
                          "-assets.i.posthog.com",
                        ) + "/static/array.js"),
                      (r =
                        t.getElementsByTagName(
                          "script",
                        )[0]).parentNode.insertBefore(p, r);
                    var u = e;
                    for (
                      void 0 !== a ? (u = e[a] = []) : (a = "posthog"),
                        u.people = u.people || [],
                        u.toString = function (t) {
                          var e = "posthog";
                          return (
                            "posthog" !== a && (e += "." + a),
                            t || (e += " (stub)"),
                            e
                          );
                        },
                        u.people.toString = function () {
                          return u.toString(1) + ".people (stub)";
                        },
                        o =
                          "init me ws ys ps bs capture je Di ks register register_once register_for_session unregister unregister_for_session Ps getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSurveysLoaded onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey canRenderSurveyAsync identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty Es $s createPersonProfile Is opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing Ss debug xs getPageViewId captureTraceFeedback captureTraceMetric".split(
                            " ",
                          ),
                        n = 0;
                      n < o.length;
                      n++
                    )
                      g(u, o[n]);
                    e._i.push([i, s, a]);
                  }),
                  (e.__SV = 1));
              })(document, window.posthog || []);
              posthog.init("phc_yJW1VjHGGwmCbbrtczfqqNxgBDbhlhOWcdzcIJEOTFE", {
                api_host: "https://us.i.posthog.com",
                person_profiles: "identified_only",
              });
            `,
          }}
        />
      </head>
      <body>
        <Providers>
          {children}
        </Providers>
        <a
          id="emergent-badge"
          target="_blank"
          rel="noopener noreferrer"
          href="https://app.emergent.sh/?utm_source=emergent-badge"
          style={{
            display: 'flex !important',
            alignItems: 'center !important',
            position: 'fixed !important',
            bottom: '20px',
            right: '20px',
            textDecoration: 'none',
            padding: '6px 10px',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif !important',
            fontSize: '12px !important',
            zIndex: '9999 !important',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15) !important',
            borderRadius: '8px !important',
            backgroundColor: '#ffffff !important',
            border: '1px solid rgba(255, 255, 255, 0.25) !important',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
            <img
              style={{ width: '20px', height: '20px', marginRight: '8px' }}
              src="https://avatars.githubusercontent.com/in/1201222?s=120&u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&v=4"
              alt="Emergent"
            />
            <p
              style={{
                color: '#000000',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif !important',
                fontSize: '12px !important',
                alignItems: 'center',
                marginBottom: 0,
              }}
            >
              Made with Emergent
            </p>
          </div>
        </a>
      </body>
    </html>
  );
}

