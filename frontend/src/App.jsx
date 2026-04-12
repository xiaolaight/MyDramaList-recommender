import { useCallback, useEffect, useState } from "react";
import { GoogleLogin } from "@react-oauth/google";

async function apiJson(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || d).join(", ")
          : res.statusText;
    throw new Error(msg || "Request failed");
  }
  return data;
}

function TrashIcon({ className }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M3 6h18" />
      <path d="M8 6V4h8v2" />
      <path d="M19 6l-1 14H6L5 6" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  );
}

function DramaGrid({ items, emptyLabel }) {
  if (!items?.length) {
    return (
      <p className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-8 text-center text-sm text-slate-500">
        {emptyLabel}
      </p>
    );
  }
  return (
    <ul className="grid gap-4 sm:grid-cols-2">
      {items.map((d) => (
        <li
          key={d.id}
          className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 shadow-lg shadow-slate-950/40"
        >
          <div className="aspect-[2/3] w-full overflow-hidden bg-slate-800">
            <img
              src={d.pic_url}
              alt=""
              className="h-full w-full object-cover"
              loading="lazy"
            />
          </div>
          <p className="p-3 text-sm font-medium leading-snug text-slate-100">
            {d.title}
          </p>
        </li>
      ))}
    </ul>
  );
}

function WatchedDramaGrid({ items, emptyLabel, disabled, onRemove }) {
  if (!items?.length) {
    return (
      <p className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-8 text-center text-sm text-slate-500">
        {emptyLabel}
      </p>
    );
  }
  return (
    <ul className="grid gap-4 sm:grid-cols-2">
      {items.map((d) => (
        <li
          key={d.id}
          className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 shadow-lg shadow-slate-950/40"
        >
          <div className="group relative aspect-[2/3] w-full overflow-hidden bg-slate-800">
            <img
              src={d.pic_url}
              alt=""
              className="h-full w-full object-cover transition duration-200 group-hover:brightness-[0.55]"
              loading="lazy"
            />
            <div
              className="pointer-events-none absolute inset-0 bg-rose-600/0 transition-colors duration-200 group-hover:bg-rose-600/35"
              aria-hidden
            />
            <button
              type="button"
              disabled={disabled}
              aria-label={`Remove ${d.title} from watched`}
              onClick={(e) => {
                e.stopPropagation();
                onRemove(d.id);
              }}
              className="absolute inset-0 z-10 flex cursor-pointer items-center justify-center opacity-0 transition-opacity duration-200 group-hover:opacity-100 disabled:cursor-not-allowed disabled:opacity-0"
            >
              <span className="rounded-full bg-rose-950/90 p-3 text-white shadow-lg ring-2 ring-rose-400/60">
                <TrashIcon className="h-8 w-8" />
              </span>
            </button>
          </div>
          <p className="p-3 text-sm font-medium leading-snug text-slate-100">
            {d.title}
          </p>
        </li>
      ))}
    </ul>
  );
}

export default function App() {
  const [view, setView] = useState("auth");
  const [credential, setCredential] = useState(null);
  const [watched, setWatched] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [authError, setAuthError] = useState("");
  const [busy, setBusy] = useState(false);

  const [searchQ, setSearchQ] = useState("");
  const [searchHits, setSearchHits] = useState([]);
  const [selected, setSelected] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [watchMsg, setWatchMsg] = useState("");

  const applyDisplayPayload = useCallback((data) => {
    setWatched(data.watched ?? []);
    setRecommendations(data.recommendations ?? []);
  }, []);

  const onSignup = async (credResponse) => {
    setAuthError("");
    setBusy(true);
    try {
      const data = await apiJson("/api/auth/signup", {
        credential: credResponse.credential,
      });
      setCredential(credResponse.credential);
      applyDisplayPayload(data);
      setView("main");
    } catch (e) {
      setAuthError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const onLogin = async (credResponse) => {
    setAuthError("");
    setBusy(true);
    try {
      const data = await apiJson("/api/auth/login", {
        credential: credResponse.credential,
      });
      setCredential(credResponse.credential);
      applyDisplayPayload(data);
      setView("main");
    } catch (e) {
      setAuthError(e.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!searchQ.trim()) {
      setSearchHits([]);
      setSelected(null);
      return;
    }
    const t = setTimeout(async () => {
      setSearchError("");
      try {
        const res = await fetch(
          `/api/search?${new URLSearchParams({ q: searchQ.trim() })}`
        );
        if (!res.ok) throw new Error("Search failed");
        const rows = await res.json();
        setSearchHits(rows);
        setSelected(null);
      } catch {
        setSearchError("Could not search.");
        setSearchHits([]);
      }
    }, 320);
    return () => clearTimeout(t);
  }, [searchQ]);

  const addWatched = async () => {
    if (!credential || !selected) return;
    setWatchMsg("");
    setBusy(true);
    try {
      const data = await apiJson("/api/watch", {
        credential,
        drama_id: selected.id,
      });
      applyDisplayPayload({
        watched: data.watched,
        recommendations: data.recommendations,
      });
      setWatchMsg(`Added “${selected.title}”.`);
      setSearchQ("");
      setSearchHits([]);
      setSelected(null);
    } catch (e) {
      setWatchMsg(e.message);
    } finally {
      setBusy(false);
    }
  };

  const removeWatched = async (dramaId) => {
    if (!credential) return;
    setWatchMsg("");
    setBusy(true);
    try {
      const data = await apiJson("/api/watch/remove", {
        credential,
        drama_id: dramaId,
      });
      applyDisplayPayload({
        watched: data.watched,
        recommendations: data.recommendations,
      });
      setWatchMsg("Removed from watched.");
    } catch (e) {
      setWatchMsg(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (view === "auth") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl shadow-violet-950/20 backdrop-blur">
          <h1 className="text-center text-2xl font-semibold tracking-tight text-white">
            Drama recommender
          </h1>
          <p className="mt-2 text-center text-sm text-slate-400">
            Sign up once, then log in anytime with the same Google account.
          </p>

          {authError ? (
            <p className="mt-4 rounded-lg border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
              {authError}
            </p>
          ) : null}

          <div className="mt-8 flex flex-col gap-4">
            <div>
              <p className="mb-2 text-center text-xs font-medium uppercase tracking-wider text-slate-500">
                Sign up
              </p>
              <div className="flex justify-center [&>div]:w-full [&_iframe]:mx-auto">
                <GoogleLogin
                  onSuccess={onSignup}
                  onError={() => setAuthError("Google sign-in failed.")}
                  text="signup_with"
                  shape="pill"
                  theme="filled_blue"
                  size="large"
                  width="100%"
                />
              </div>
            </div>
            <div className="relative">
              <div
                className="absolute inset-x-0 top-0 flex items-center"
                aria-hidden
              >
                <div className="w-full border-t border-slate-800" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-slate-900/90 px-2 text-slate-500">
                  or
                </span>
              </div>
            </div>
            <div>
              <p className="mb-2 text-center text-xs font-medium uppercase tracking-wider text-slate-500">
                Log in
              </p>
              <div className="flex justify-center [&>div]:w-full [&_iframe]:mx-auto">
                <GoogleLogin
                  onSuccess={onLogin}
                  onError={() => setAuthError("Google sign-in failed.")}
                  text="signin_with"
                  shape="pill"
                  theme="filled_black"
                  size="large"
                  width="100%"
                />
              </div>
            </div>
          </div>

          {busy ? (
            <p className="mt-6 text-center text-xs text-slate-500">
              Talking to server…
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-10">
      <header className="mx-auto mb-10 max-w-6xl">
        <h1 className="text-2xl font-semibold text-white sm:text-3xl">
          Your library
        </h1>
        <p className="mt-1 text-slate-400">
          Watched titles and personalized recommendations.
        </p>
      </header>

      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-2">
        <section>
          <h2 className="mb-4 text-lg font-semibold text-violet-200">
            Watched dramas
          </h2>

          <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
              Search dramas
            </label>
            <input
              type="search"
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              placeholder="Type a title…"
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
            />
            {searchError ? (
              <p className="mt-2 text-xs text-rose-400">{searchError}</p>
            ) : null}
            {searchHits.length > 0 ? (
              <ul className="mt-3 max-h-48 overflow-auto rounded-lg border border-slate-800">
                {searchHits.map((row) => (
                  <li key={row.id}>
                    <button
                      type="button"
                      onClick={() => setSelected(row)}
                      className={`flex w-full items-center px-3 py-2 text-left text-sm transition hover:bg-slate-800 ${
                        selected?.id === row.id
                          ? "bg-violet-950/50 text-violet-100"
                          : "text-slate-200"
                      }`}
                    >
                      {row.title}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            <button
              type="button"
              disabled={!selected || busy}
              onClick={addWatched}
              className="mt-4 w-full rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Add to watched
            </button>
            {watchMsg ? (
              <p className="mt-2 text-xs text-slate-400">{watchMsg}</p>
            ) : null}
          </div>

          <WatchedDramaGrid
            items={watched}
            emptyLabel="No watched dramas yet. Search above and add some."
            disabled={busy}
            onRemove={removeWatched}
          />
        </section>

        <section>
          <h2 className="mb-4 text-lg font-semibold text-emerald-200/90">
            Recommendations
          </h2>
          <DramaGrid
            items={recommendations}
            emptyLabel="Recommendations appear after you add watched dramas."
          />
        </section>
      </div>
    </div>
  );
}
