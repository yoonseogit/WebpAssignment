import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  Bookmark,
  Bot,
  LogOut,
  Moon,
  RefreshCw,
  Search,
  Star,
  Sun,
  Trash2,
  TrendingUp,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { clearStoredAuth, getStoredAuth, request, setStoredAuth } from "./api";
import "./styles.css";

function formatPrice(value) {
  return Number(value).toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

function formatPercent(value) {
  return `${Number(value).toFixed(2)}%`;
}

function App() {
  const [auth, setAuth] = useState(getStoredAuth());
  const [config, setConfig] = useState({ app_name: "CoinSight", max_favorite_markets: 5, analysis_cache_minutes: 30 });
  const [markets, setMarkets] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [analyses, setAnalyses] = useState(() => {
    const raw = sessionStorage.getItem("coinsight:lastAnalyses");
    return raw ? JSON.parse(raw) : [];
  });
  const [query, setQuery] = useState(localStorage.getItem("coinsight:query") || "");
  const [sortMode, setSortMode] = useState(localStorage.getItem("coinsight:sort") || "volatility");
  const [theme, setTheme] = useState(localStorage.getItem("coinsight:theme") || "dark");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("coinsight:theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("coinsight:query", query);
  }, [query]);

  useEffect(() => {
    localStorage.setItem("coinsight:sort", sortMode);
  }, [sortMode]);

  async function bootstrap() {
    setLoading(true);
    try {
      const [configData, marketData] = await Promise.all([
        request("/api/config"),
        request("/api/markets/volatility"),
      ]);
      setConfig(configData);
      setMarkets(marketData);
      if (auth) {
        setFavorites(await request("/api/favorites"));
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bootstrap();
  }, [auth?.access_token]);

  const filteredMarkets = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    const list = markets.filter((item) => {
      if (!keyword) return true;
      return (
        item.market.toLowerCase().includes(keyword) ||
        item.korean_name.toLowerCase().includes(keyword) ||
        item.english_name.toLowerCase().includes(keyword)
      );
    });
    return [...list].sort((a, b) => {
      if (sortMode === "change") return Math.abs(b.signed_change_rate) - Math.abs(a.signed_change_rate);
      if (sortMode === "volume") return b.acc_trade_price_24h - a.acc_trade_price_24h;
      return b.volatility_pct - a.volatility_pct;
    });
  }, [markets, query, sortMode]);

  const chartData = filteredMarkets.slice(0, 10).map((item) => ({
    name: item.market.replace("KRW-", ""),
    volatility: item.volatility_pct,
  }));

  async function handleAuth(event, mode) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const data = await request(`/api/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      setStoredAuth(data);
      setAuth(data);
      setMessage(mode === "register" ? "회원가입이 완료되었습니다." : "로그인되었습니다.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function addFavorite(market) {
    if (!auth) {
      setMessage("로그인 후 관심 종목을 추가할 수 있습니다.");
      return;
    }
    try {
      const created = await request("/api/favorites", {
        method: "POST",
        body: JSON.stringify({
          market: market.market,
          korean_name: market.korean_name,
          english_name: market.english_name,
        }),
      });
      setFavorites((items) => [...items, created]);
      setMessage(`${market.korean_name}을 관심 종목에 추가했습니다.`);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function removeFavorite(market) {
    try {
      await request(`/api/favorites/${market}`, { method: "DELETE" });
      setFavorites((items) => items.filter((item) => item.market !== market));
      setAnalyses((items) => {
        const next = items.filter((item) => item.market !== market);
        sessionStorage.setItem("coinsight:lastAnalyses", JSON.stringify(next));
        return next;
      });
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function analyzeFavorites() {
    setLoading(true);
    try {
      const data = await request("/api/analysis/favorites", { method: "POST" });
      setAnalyses(data.analyses);
      sessionStorage.setItem("coinsight:lastAnalyses", JSON.stringify(data.analyses));
      setMessage("관심 종목 분석이 완료되었습니다.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearStoredAuth();
    setAuth(null);
    setFavorites([]);
    setAnalyses([]);
    sessionStorage.removeItem("coinsight:lastAnalyses");
  }

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <span className="eyebrow">Upbit volatility monitor</span>
          <h1>CoinSight</h1>
        </div>
        <div className="top-actions">
          <button className="icon-button" title="테마 전환" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          {auth && (
            <button className="ghost-button" onClick={logout}>
              <LogOut size={16} />
              로그아웃
            </button>
          )}
        </div>
      </header>

      {message && <div className="notice">{message}</div>}

      {!auth && (
        <section className="auth-grid">
          <AuthPanel title="로그인" submitLabel="로그인" onSubmit={(event) => handleAuth(event, "login")} />
          <AuthPanel title="회원가입" submitLabel="가입" onSubmit={(event) => handleAuth(event, "register")} />
        </section>
      )}

      <section className="summary-grid">
        <Metric icon={<BarChart3 />} label="KRW 종목" value={`${markets.length}개`} />
        <Metric icon={<Star />} label="관심 종목" value={`${favorites.length} / ${config.max_favorite_markets}`} />
        <Metric icon={<Bot />} label="분석 캐시" value={`${config.analysis_cache_minutes}분`} />
      </section>

      <section className="workspace">
        <div className="panel market-panel">
          <div className="panel-header">
            <div>
              <h2>변동성 순위</h2>
              <p>고가와 저가의 차이를 현재가 기준으로 계산합니다.</p>
            </div>
            <button className="icon-button" title="새로고침" onClick={bootstrap} disabled={loading}>
              <RefreshCw size={18} />
            </button>
          </div>

          <div className="controls">
            <label className="search-box">
              <Search size={17} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="종목 검색" />
            </label>
            <div className="segmented">
              <button className={sortMode === "volatility" ? "active" : ""} onClick={() => setSortMode("volatility")}>변동성</button>
              <button className={sortMode === "change" ? "active" : ""} onClick={() => setSortMode("change")}>등락</button>
              <button className={sortMode === "volume" ? "active" : ""} onClick={() => setSortMode("volume")}>거래대금</button>
            </div>
          </div>

          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="volatility" fill="#14b8a6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="market-list">
            {filteredMarkets.slice(0, 30).map((item, index) => {
              const isFavorite = favorites.some((favorite) => favorite.market === item.market);
              const disabled = !isFavorite && favorites.length >= config.max_favorite_markets;
              return (
                <article className="market-row" key={item.market}>
                  <span className="rank">{index + 1}</span>
                  <div className="market-name">
                    <strong>{item.korean_name}</strong>
                    <span>{item.market}</span>
                  </div>
                  <div className="market-stats">
                    <strong>{formatPercent(item.volatility_pct)}</strong>
                    <span>{formatPrice(item.trade_price)} KRW</span>
                  </div>
                  <button
                    className={isFavorite ? "icon-button selected" : "icon-button"}
                    title="관심 종목 추가"
                    disabled={isFavorite || disabled}
                    onClick={() => addFavorite(item)}
                  >
                    <Bookmark size={17} />
                  </button>
                </article>
              );
            })}
          </div>
        </div>

        <aside className="side-column">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>관심 종목</h2>
                <p>최대 {config.max_favorite_markets}개까지 등록할 수 있습니다.</p>
              </div>
            </div>
            <div className="favorite-list">
              {favorites.length === 0 && <p className="empty">관심 종목을 추가해 주세요.</p>}
              {favorites.map((item) => (
                <div className="favorite-chip" key={item.market}>
                  <div>
                    <strong>{item.korean_name}</strong>
                    <span>{item.market}</span>
                  </div>
                  <button className="icon-button" title="삭제" onClick={() => removeFavorite(item.market)}>
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
            <button className="primary-button" onClick={analyzeFavorites} disabled={!auth || favorites.length === 0 || loading}>
              <TrendingUp size={18} />
              GPT 요약 분석
            </button>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>분석 결과</h2>
                <p>sessionStorage에 마지막 결과를 임시 보관합니다.</p>
              </div>
            </div>
            <div className="analysis-list">
              {analyses.length === 0 && <p className="empty">아직 분석 결과가 없습니다.</p>}
              {analyses.map((item) => (
                <article className="analysis-card" key={`${item.market}-${item.created_at}`}>
                  <div className="analysis-head">
                    <strong>{item.korean_name}</strong>
                    <span>{item.cached ? "캐시" : "신규"}</span>
                  </div>
                  <p>{item.summary}</p>
                  <div className="analysis-meta">
                    <span>{item.trend}</span>
                    <span>변동성 {formatPercent(item.volatility_score)}</span>
                  </div>
                  <small>{item.risk_note}</small>
                </article>
              ))}
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}

function AuthPanel({ title, submitLabel, onSubmit }) {
  return (
    <form className="panel auth-panel" onSubmit={onSubmit}>
      <h2>{title}</h2>
      <input name="email" type="email" placeholder="email@example.com" required />
      <input name="password" type="password" placeholder="비밀번호 6자 이상" required minLength={6} />
      <button className="primary-button" type="submit">{submitLabel}</button>
    </form>
  );
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
