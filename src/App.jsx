import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  Shield, 
  Search, 
  RefreshCw, 
  Calendar, 
  ExternalLink, 
  AlertCircle, 
  CheckCircle, 
  Eye, 
  ChevronDown, 
  ChevronUp, 
  FileText,
  Mail,
  Webhook,
  MessageSquare,
  Send,
  X
} from 'lucide-react';

function App() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isScraping, setIsScraping] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [expandedId, setExpandedId] = useState(null);
  
  // Custom toast notification state
  const [toast, setToast] = useState({
    show: false,
    policyName: '',
    oldStatus: '',
    newStatus: ''
  });

  // Chatbot states
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      sender: 'assistant',
      text: "Hi! I'm your Policy Assistant. Ask me questions about global AI regulations (e.g., 'What are the obligations under the EU AI Act?' or 'What are India's AI guidelines?')."
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { sender: 'user', text: userMessage }]);
    setIsTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });
      if (res.ok) {
        const data = await res.json();
        setChatHistory(prev => [...prev, { sender: 'assistant', text: data.response }]);
      } else {
        setChatHistory(prev => [...prev, { sender: 'assistant', text: "Sorry, I encountered an error communicating with the chat engine." }]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setChatHistory(prev => [...prev, { sender: 'assistant', text: "Connection error. Make sure the server is running." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/policies');
      if (res.ok) {
        const data = await res.json();
        setPolicies(data);
      } else {
        console.error("Failed to fetch policies");
      }
    } catch (err) {
      console.error("Error fetching policies:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleScrape = async () => {
    setIsScraping(true);
    try {
      const res = await fetch('/api/policies/scrape', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.updated_count > 0) {
          // If status updates occurred, show toast for the first one
          const firstUpdate = data.updates[0];
          showToast(firstUpdate.policy_name, firstUpdate.old_status, firstUpdate.new_status);
        } else {
          showToast("Scraper completed", "No new updates", "Synced");
        }
        fetchPolicies();
      } else {
        console.error("Scraper request failed");
      }
    } catch (err) {
      console.error("Error triggering scrape:", err);
    } finally {
      setIsScraping(false);
    }
  };

  const handleStatusChange = async (policyId, currentStatus, newStatus) => {
    if (currentStatus === newStatus) return;
    
    // Find the policy item to get its name for the toast
    const policy = policies.find(p => p.policy_id === policyId);
    const policyName = policy ? policy.policy_name : 'Policy';
    
    try {
      const res = await fetch('/api/policies/update-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_id: policyId, status: newStatus })
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          showToast(policyName, currentStatus, newStatus);
          fetchPolicies();
        }
      }
    } catch (err) {
      console.error("Error updating status:", err);
    }
  };

  const showToast = (name, oldStat, newStat) => {
    setToast({
      show: true,
      policyName: name,
      oldStatus: oldStat,
      newStatus: newStat
    });
    // Auto hide toast after 6 seconds
    setTimeout(() => {
      setToast(prev => ({ ...prev, show: false }));
    }, 6000);
  };

  // Filter Logic
  const filteredPolicies = policies.filter(policy => {
    const matchesSearch = 
      policy.policy_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      policy.summary_ai_generated.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesJurisdiction = jurisdictionFilter === 'All' || policy.jurisdiction === jurisdictionFilter;
    const matchesStatus = statusFilter === 'All' || policy.status === statusFilter;
    
    return matchesSearch && matchesJurisdiction && matchesStatus;
  });

  // Stats Counters
  const totalCount = policies.length;
  const enforcedCount = policies.filter(p => p.status === 'Enforced').length;
  const reviewCount = policies.filter(p => p.status === 'Under Review').length;
  const proposedCount = policies.filter(p => p.status === 'Proposed' || p.status === 'Passed').length;

  // Helper to get status badge class
  const getStatusBadge = (status) => {
    const s = status.toLowerCase();
    if (s === 'enforced') return 'badge enforced';
    if (s === 'under review') return 'badge under-review';
    if (s === 'passed') return 'badge passed';
    return 'badge proposed'; // Proposed / Draft
  };

  // Helper to format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return dateStr;
    }
  };

  // Static timeline data representing core global milestones
  const milestones = [
    { date: "June 2026", title: "US EO 14409 In Effect", desc: "Frontier AI models require voluntary benchmarking and security checks.", active: true },
    { date: "August 2024", title: "EU AI Act Enforcement Starts", desc: "The regulation enters into force with a phased implementation over 24 months.", active: true },
    { date: "December 2025", title: "US Policy Framework Signed", desc: "EO 14365 establishing standard federal AI evaluation criteria.", active: true },
    { date: "July 2025", title: "US Export Stack Order", desc: "EO 14320 regulating exports of AI technology and compute assets.", active: true },
    { date: "Late 2024", title: "UK Code of Practice Draft", desc: "DSIT issues voluntary safety guidelines for generative AI developers.", active: false }
  ];

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-section">
          <Globe className="brand-logo" size={32} />
          <div>
            <h1 className="brand-title">Lexis AI Policy Center</h1>
            <p className="brand-subtitle">Global AI Regulations & Executive Orders</p>
          </div>
        </div>
        <div className="actions-section">
          <button 
            className="btn-glow" 
            onClick={handleScrape} 
            disabled={isScraping}
          >
            <RefreshCw className={isScraping ? "spin" : ""} size={18} />
            {isScraping ? "Scanning Sources..." : "Scan for Updates"}
          </button>
        </div>
      </header>

      {/* Stats Cards */}
      <section className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon-container primary">
            <Globe size={24} />
          </div>
          <div>
            <div className="stat-value">{totalCount}</div>
            <div className="stat-label">Tracked Regulations</div>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon-container success">
            <CheckCircle size={24} />
          </div>
          <div>
            <div className="stat-value">{enforcedCount}</div>
            <div className="stat-label">Enforced Policies</div>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon-container warning">
            <AlertCircle size={24} />
          </div>
          <div>
            <div className="stat-value">{reviewCount}</div>
            <div className="stat-label">Under Review</div>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon-container secondary">
            <Shield size={24} />
          </div>
          <div>
            <div className="stat-value">{proposedCount}</div>
            <div className="stat-label">Proposed / Passed</div>
          </div>
        </div>
      </section>

      {/* Interactive Map Highlights */}
      <section className="glass-panel map-banner">
        <div className="map-bg-pattern"></div>
        <div className="map-details">
          <h2 className="map-title">Global Legislative Hotspots</h2>
          <p className="map-desc">
            Monitoring active updates across prime regulatory centers. Changes to policy status trigger mock webhooks and email notification payloads locally.
          </p>
        </div>
        <div className="map-hotspots" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: 'var(--color-primary)'}}></span>
            <span>US: {policies.filter(p => p.jurisdiction === 'US').length}</span>
          </div>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: 'var(--color-secondary)'}}></span>
            <span>EU: {policies.filter(p => p.jurisdiction === 'EU').length}</span>
          </div>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: 'var(--color-success)'}}></span>
            <span>UK: {policies.filter(p => p.jurisdiction === 'UK').length}</span>
          </div>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: 'var(--color-warning)'}}></span>
            <span>India: {policies.filter(p => p.jurisdiction === 'India').length}</span>
          </div>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: '#ef4444'}}></span>
            <span>China: {policies.filter(p => p.jurisdiction === 'China').length}</span>
          </div>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: '#eab308'}}></span>
            <span>Canada: {policies.filter(p => p.jurisdiction === 'Canada').length}</span>
          </div>
          <div className="hotspot">
            <span className="hotspot-dot" style={{color: 'var(--text-secondary)'}}></span>
            <span>Global: {policies.filter(p => p.jurisdiction === 'Global').length}</span>
          </div>
        </div>
      </section>

      {/* Filter and Control Bar */}
      <section className="glass-panel control-bar">
        <div className="search-input-wrapper">
          <Search className="search-icon" size={18} />
          <input 
            type="text" 
            placeholder="Search policy name or summary keywords..." 
            className="input-field"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <select 
          className="select-field"
          value={jurisdictionFilter}
          onChange={(e) => setJurisdictionFilter(e.target.value)}
        >
          <option value="All">All Jurisdictions</option>
          <option value="US">United States (US)</option>
          <option value="EU">European Union (EU)</option>
          <option value="UK">United Kingdom (UK)</option>
          <option value="India">India</option>
          <option value="China">China</option>
          <option value="Canada">Canada</option>
          <option value="Global">Global / OECD</option>
        </select>
        <select 
          className="select-field"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="All">All Statuses</option>
          <option value="Proposed">Proposed</option>
          <option value="Under Review">Under Review</option>
          <option value="Passed">Passed</option>
          <option value="Enforced">Enforced</option>
        </select>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Showing {filteredPolicies.length} of {totalCount}
        </div>
      </section>

      {/* Dashboard Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Policies List */}
        <main>
          <div className="policy-list-header">
            <h2>Regulatory Policies & Directives</h2>
          </div>

          {loading ? (
            <div className="glass-panel empty-state">
              <RefreshCw className="spin empty-icon" size={32} />
              <p>Fetching regulation documents...</p>
            </div>
          ) : filteredPolicies.length === 0 ? (
            <div className="glass-panel empty-state">
              <AlertCircle className="empty-icon" size={32} />
              <p>No policy documents match the current filters.</p>
            </div>
          ) : (
            <div className="policy-list-container">
              {filteredPolicies.map((policy) => {
                const isExpanded = expandedId === policy.policy_id;
                const cardClass = `glass-panel policy-card ${policy.jurisdiction.toLowerCase()}`;
                
                return (
                  <article key={policy.policy_id} className={cardClass}>
                    <div className="policy-card-header">
                      <div className="policy-title-block">
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span className="badge region">{policy.jurisdiction}</span>
                          <span className={getStatusBadge(policy.status)}>{policy.status}</span>
                        </div>
                        <h3 
                          className="policy-card-title"
                          onClick={() => setExpandedId(isExpanded ? null : policy.policy_id)}
                        >
                          {policy.policy_name}
                        </h3>
                      </div>
                      <button 
                        className="btn-status-change"
                        style={{ border: 'none', background: 'none' }}
                        onClick={() => setExpandedId(isExpanded ? null : policy.policy_id)}
                      >
                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </button>
                    </div>

                    <div className="policy-meta-row">
                      <span className="policy-meta-item">
                        <Calendar size={12} />
                        Last Updated: {formatDate(policy.last_updated)}
                      </span>
                      <span className="policy-meta-item">
                        <ExternalLink size={12} />
                        <a href={policy.source_url} target="_blank" rel="noopener noreferrer">Official Portal</a>
                      </span>
                    </div>

                    {isExpanded && (
                      <div className="policy-card-body">
                        {/* 1. Quick Metadata Grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Authority / Source:</strong> 
                            <p style={{ color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                              {policy.source_url.includes('whitehouse.gov') ? 'Executive Office of the President (US)' : 
                               policy.source_url.includes('federalregister') ? 'Federal Register (US)' :
                               policy.source_url.includes('meity.gov.in') ? 'MeitY (Government of India)' :
                               policy.source_url.includes('cac.gov.cn') ? 'Cyberspace Administration (China)' :
                               policy.source_url.includes('canada.ca') ? 'ISED (Government of Canada)' :
                               policy.source_url.includes('oecd.org') ? 'OECD legal compendium' :
                               'Official Regulatory Agency'}
                            </p>
                          </div>
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Compliance Level:</strong>
                            <p style={{ color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                              {policy.status === 'Enforced' ? 'Mandatory - Strict Audit' : 
                               policy.status === 'Passed' ? 'Awaiting Enforcement Date' :
                               policy.status === 'Under Review' ? 'Recommended Practices' :
                               'Proposed - Watchlist'}
                            </p>
                          </div>
                        </div>

                        {/* 2. Scrollable summary container */}
                        <h4 style={{ fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-primary)' }}>Regulation Summary & Scope</h4>
                        <div className="markdown-content-scrollable">
                          {policy.summary_ai_generated.split('\n').map((line, idx) => {
                            if (line.startsWith('### ')) {
                              return <h3 key={idx} style={{ fontSize: '0.9rem', color: 'var(--text-primary)', margin: '0.5rem 0 0.25rem 0' }}>{line.replace('### ', '')}</h3>;
                            }
                            if (line.startsWith('**') && line.endsWith('**')) {
                              return <p key={idx} style={{ marginTop: '0.5rem', fontWeight: 'bold', color: 'var(--text-primary)', fontSize: '0.8rem' }}>{line.replace(/\*\*/g, '')}</p>;
                            }
                            if (line.startsWith('- ')) {
                              return <li key={idx} style={{ marginLeft: '1rem', listStyleType: 'disc', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{line.replace('- ', '')}</li>;
                            }
                            return line.trim() !== '' ? <p key={idx} style={{ margin: '0.25rem 0', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{line}</p> : null;
                          })}
                        </div>

                        {/* 3. Interactive Compliance Checklist */}
                        <h4 style={{ fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--text-primary)', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>Compliance Checklist</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '1rem' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                            <input type="checkbox" defaultChecked={policy.status === 'Enforced'} style={{ accentColor: 'var(--color-primary)' }} />
                            Audit active models against safety & bias metrics
                          </label>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                            <input type="checkbox" defaultChecked={policy.status === 'Enforced'} style={{ accentColor: 'var(--color-primary)' }} />
                            Verify watermarking/logging configurations for generative outputs
                          </label>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                            <input type="checkbox" style={{ accentColor: 'var(--color-primary)' }} />
                            Submit registry filing to {policy.jurisdiction} data authorities
                          </label>
                        </div>

                        {/* Overriding Status Ingestion Controls */}
                        <div className="card-actions">
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: 'auto', alignSelf: 'center' }}>
                            Force Status Transition:
                          </span>
                          {['Proposed', 'Under Review', 'Passed', 'Enforced'].map((s) => (
                            <button
                              key={s}
                              className={`btn-status-change ${policy.status === s ? 'active' : ''}`}
                              onClick={() => handleStatusChange(policy.policy_id, policy.status, s)}
                            >
                              {s}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </main>

        {/* Right Column: Timelines & Auditing */}
        <aside>
          <div className="glass-panel timeline-card">
            <h2 className="timeline-title">
              <Calendar size={20} className="brand-logo" />
              Compliance Timeline
            </h2>
            <div className="timeline-container">
              {milestones.map((milestone, idx) => (
                <div key={idx} className={`timeline-item ${milestone.active ? 'active' : ''}`}>
                  <div className="timeline-marker"></div>
                  <div className="timeline-date">{milestone.date}</div>
                  <div className="timeline-content-title">{milestone.title}</div>
                  <div className="timeline-content-desc">{milestone.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* Notification Toast Trigger Alert */}
      {toast.show && (
        <div className="alert-popup-toast">
          <div style={{ color: 'var(--color-primary)' }}>
            <Webhook size={24} style={{ filter: 'drop-shadow(0 0 6px var(--color-primary-glow))' }} />
          </div>
          <div style={{ flex: 1 }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-primary)', display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
              <span className="badge region">Status Event Dispatched</span>
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Policy <strong>{toast.policyName}</strong> changed from <em>{toast.oldStatus}</em> to <em>{toast.newStatus}</em>.
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.15rem' }}>
                <Webhook size={10} /> Webhook logged
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.15rem' }}>
                <Mail size={10} /> Email body logged
              </span>
            </div>
          </div>
          <button className="toast-close" onClick={() => setToast(prev => ({ ...prev, show: false }))}>
            &times;
          </button>
        </div>
      )}

      {/* Floating Chat Widget */}
      <div className="chatbot-widget">
        {isChatOpen ? (
          <div className="glass-panel chat-window">
            <div className="chat-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <MessageSquare size={16} className="brand-logo" />
                <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Policy Assistant</span>
              </div>
              <button className="chat-close-btn" onClick={() => setIsChatOpen(false)}>
                <X size={16} />
              </button>
            </div>
            
            <div className="chat-messages">
              {chatHistory.map((msg, index) => (
                <div key={index} className={`chat-bubble-wrapper ${msg.sender}`}>
                  <div className={`chat-bubble ${msg.sender}`}>
                    {msg.sender === 'user' ? (
                      <p style={{ margin: 0, fontSize: '0.8rem', wordBreak: 'break-word', color: '#ffffff' }}>
                        {msg.text}
                      </p>
                    ) : (
                      <div 
                        className="chat-assistant-content"
                        style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}
                        dangerouslySetInnerHTML={{ __html: msg.text }}
                      />
                    )}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="chat-bubble-wrapper assistant">
                  <div className="chat-bubble assistant typing">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSendMessage} className="chat-input-area">
              <input 
                type="text" 
                placeholder="Ask a question..." 
                className="input-field chat-input"
                style={{ paddingLeft: '1rem' }}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
              />
              <button type="submit" className="btn-glow chat-send-btn" style={{ padding: '0.5rem 0.75rem', height: 'auto' }}>
                <Send size={12} />
              </button>
            </form>
          </div>
        ) : (
          <button className="chat-toggle-btn" onClick={() => setIsChatOpen(true)}>
            <MessageSquare size={24} />
          </button>
        )}
      </div>
    </div>
  );
}

export default App;
