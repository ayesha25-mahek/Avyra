import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  CheckCircle2,
  Clock,
  FileText,
  Download,
  RefreshCw,
  Sparkles,
  XCircle,
  Check,
  RotateCcw,
} from 'lucide-react';
import { fetchGeneratedFiles, downloadFile, type GeneratedFileInfo } from '@/lib/api';
import type { UserProfile, OrgConfig } from '@/types/auth';

interface ReviewItem {
  id: string;
  title: string;
  category: 'inspection' | 'engineering' | 'data';
  status: 'pending_approval' | 'approved' | 'revision_requested' | 'rejected';
  submitted_by: string;
  submitted_at: string;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  deliverables: string[];
  summary: string;
  decision_comments?: string;
  decision_timestamp?: string;
}

interface ManagerOverviewViewProps {
  user?: UserProfile | null;
  orgConfig?: OrgConfig | null;
}

export const ManagerOverviewView: React.FC<ManagerOverviewViewProps> = ({ user }) => {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [authorizedFiles, setAuthorizedFiles] = useState<GeneratedFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedReview, setSelectedReview] = useState<ReviewItem | null>(null);
  const [actionComments, setActionComments] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      // 1. Fetch pending reviews from backend
      const res = await fetch('/api/manager/reviews');
      if (res.ok) {
        const data = await res.json();
        setReviews(data.reviews || []);
        if (data.reviews && data.reviews.length > 0 && !selectedReview) {
          setSelectedReview(data.reviews[0]);
        }
      }

      // 2. Fetch authorized files
      const filesRes = await fetchGeneratedFiles();
      setAuthorizedFiles(filesRes || []);
    } catch (err) {
      console.error('Failed to load manager records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleReviewAction = async (action: 'approve' | 'request_revision' | 'reject') => {
    if (!selectedReview) return;
    setActionLoading(true);
    setActionSuccessMsg(null);
    try {
      const res = await fetch('/api/manager/reviews/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          review_id: selectedReview.id,
          action,
          comments: actionComments,
          reviewer_role: user?.role || 'manager',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setActionSuccessMsg(`Action '${action.replace('_', ' ')}' recorded successfully.`);
        // Update review in state
        setReviews((prev) =>
          prev.map((r) => (r.id === selectedReview.id ? data.review : r))
        );
        setSelectedReview(data.review);
        setActionComments('');
      }
    } catch (err) {
      console.error('Action failed:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredReviews = reviews.filter((r) => {
    if (filterCategory !== 'all' && r.category !== filterCategory) return false;
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    return true;
  });

  const pendingCount = reviews.filter((r) => r.status === 'pending_approval').length;
  const approvedCount = reviews.filter((r) => r.status === 'approved').length;
  const highRiskCount = reviews.filter((r) => r.risk_level === 'HIGH' || r.risk_level === 'CRITICAL').length;

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-6xl mx-auto">
      {/* Header */}
      <div className="pb-4 border-b border-[#1A402D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
              EXECUTIVE WORKSPACE
            </span>
            <span className="text-xs text-[#74C69D] font-mono">Role: Asset Manager</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Briefcase className="w-6 h-6 text-[#00E599]" />
            Manager Overview &amp; Review Approvals
          </h1>
          <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
            Executive oversight across authorized refinery units, inspection deliverables, evidence-grounded action priorities, and pending human sign-offs.
          </p>
        </div>

        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          className="self-start sm:self-auto px-3.5 py-1.5 rounded-lg bg-[#0E2419] hover:bg-[#143324] border border-[#1E4D36] text-xs font-mono text-[#00E599] flex items-center gap-2 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Sync Records</span>
        </button>
      </div>

      {/* KPI Headline Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-1">
          <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider">Pending Sign-Offs</span>
          <div className="text-2xl font-bold text-[#F59E0B] font-mono">{pendingCount}</div>
          <p className="text-[11px] text-[#587E6B]">Requires manager approval</p>
        </div>

        <div className="p-4 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-1">
          <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider">Approved Deliverables</span>
          <div className="text-2xl font-bold text-[#00E599] font-mono">{approvedCount}</div>
          <p className="text-[11px] text-[#587E6B]">Archived with audit stamp</p>
        </div>

        <div className="p-4 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-1">
          <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider">High / Critical Hazards</span>
          <div className="text-2xl font-bold text-[#EF4444] font-mono">{highRiskCount}</div>
          <p className="text-[11px] text-[#587E6B]">Exceeding standard tolerances</p>
        </div>

        <div className="p-4 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-1">
          <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider">Authorized Records</span>
          <div className="text-2xl font-bold text-[#38BDF8] font-mono">{authorizedFiles.length}</div>
          <p className="text-[11px] text-[#587E6B]">Stored in local confidential vault</p>
        </div>
      </div>

      {/* Main Review Tracker & Detail Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Pending Review List (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#1A402D]">
            <h2 className="text-sm font-bold text-white font-mono flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-[#00E599]" />
              Human Review Backlog ({filteredReviews.length})
            </h2>

            {/* Filters */}
            <div className="flex items-center gap-1 text-[11px] font-mono">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="bg-[#050F09] border border-[#1E4D36] text-[#74C69D] rounded px-2 py-1 text-[10px]"
              >
                <option value="all">All Status</option>
                <option value="pending_approval">Pending</option>
                <option value="approved">Approved</option>
                <option value="revision_requested">Revision</option>
              </select>
            </div>
          </div>

          <div className="space-y-2.5 max-h-[600px] overflow-y-auto scrollbar-thin pr-1">
            {filteredReviews.map((rev) => {
              const isSelected = selectedReview?.id === rev.id;
              const isCrit = rev.risk_level === 'CRITICAL' || rev.risk_level === 'HIGH';
              return (
                <div
                  key={rev.id}
                  onClick={() => {
                    setSelectedReview(rev);
                    setActionSuccessMsg(null);
                  }}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#143324] border-[#00E599] shadow-lg'
                      : 'bg-[#091A11] border-[#183B28] hover:bg-[#0E2419]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold ${
                        rev.status === 'approved'
                          ? 'bg-[#00E599]/20 text-[#00E599] border border-[#00E599]/40'
                          : rev.status === 'revision_requested'
                          ? 'bg-amber-950/60 text-amber-400 border border-amber-800'
                          : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                      }`}
                    >
                      {rev.status.replace('_', ' ').toUpperCase()}
                    </span>

                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                        isCrit ? 'bg-red-950/80 text-red-400 font-bold' : 'bg-[#163826] text-[#74C69D]'
                      }`}
                    >
                      {rev.risk_level} RISK
                    </span>
                  </div>

                  <h3 className="text-xs font-semibold text-white leading-snug line-clamp-2">
                    {rev.title}
                  </h3>

                  <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-[#587E6B]">
                    <span>By: {rev.submitted_by.split('@')[0]}</span>
                    <span>{rev.submitted_at.split(' ')[0]}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Review Sign-off Workspace (7 cols) */}
        <div className="lg:col-span-7">
          {selectedReview ? (
            <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-5">
              <div className="flex items-start justify-between gap-3 pb-3 border-b border-[#1A402D]">
                <div>
                  <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider">
                    REVIEW ITEM: {selectedReview.id}
                  </span>
                  <h2 className="text-lg font-bold text-white leading-tight mt-0.5">
                    {selectedReview.title}
                  </h2>
                  <div className="mt-1 flex items-center gap-3 text-xs font-mono text-[#9DC4B0]">
                    <span>Category: <strong>{selectedReview.category.toUpperCase()}</strong></span>
                    <span>•</span>
                    <span>Submitted: {selectedReview.submitted_at}</span>
                  </div>
                </div>

                <span
                  className={`text-xs font-mono px-2.5 py-1 rounded-lg border font-bold ${
                    selectedReview.status === 'approved'
                      ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40'
                      : 'bg-amber-950/60 text-amber-400 border-amber-800'
                  }`}
                >
                  {selectedReview.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              {/* Summary Description */}
              <div className="p-4 rounded-xl bg-[#06120B] border border-[#163827] space-y-2">
                <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider font-semibold">
                  Grounded Technical Findings &amp; Evidence
                </span>
                <p className="text-xs sm:text-sm text-gray-200 leading-relaxed font-sans">
                  {selectedReview.summary}
                </p>
              </div>

              {/* Attached Deliverables */}
              <div className="space-y-2">
                <span className="text-xs font-mono text-[#74C69D] uppercase tracking-wider font-semibold block">
                  Attached Deliverables &amp; Artifacts
                </span>
                <div className="flex flex-wrap gap-2">
                  {selectedReview.deliverables.map((d, i) => (
                    <div
                      key={i}
                      className="px-3 py-1.5 rounded-lg bg-[#0E2419] border border-[#1E4D36] text-xs font-mono text-white flex items-center gap-2"
                    >
                      <FileText className="w-3.5 h-3.5 text-[#00E599]" />
                      <span>{d}</span>
                      <button
                        type="button"
                        onClick={() => downloadFile(`/files/documents/${d}`, d)}
                        className="text-[#00E599] hover:text-white"
                        title="Download Deliverable"
                      >
                        <Download className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Review Decision Form */}
              <div className="p-4 rounded-xl bg-[#08170F] border border-[#1E4D36] space-y-3">
                <label className="block text-xs font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#00E599]" />
                  Manager Sign-Off &amp; Action Directives
                </label>

                <textarea
                  rows={3}
                  placeholder="Record formal manager sign-off notes, conditions of acceptance, or specific revision directives…"
                  value={actionComments}
                  onChange={(e) => setActionComments(e.target.value)}
                  className="w-full rounded-lg bg-[#050F09] border border-[#1E4D36] p-3 text-xs text-gray-200 focus:outline-none focus:border-[#00E599] font-serif"
                />

                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => handleReviewAction('approve')}
                    disabled={actionLoading || selectedReview.status === 'approved'}
                    className="flex-1 py-2.5 px-4 rounded-full bg-[#52B788] hover:bg-[#74C69D] text-[#07130D] text-xs font-bold font-mono flex items-center justify-center gap-1.5 disabled:opacity-40 transition-all active:scale-[0.98] shadow-sm hover:shadow-[0_0_14px_rgba(82,183,136,0.35)]"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Formal Sign-Off (Approve)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleReviewAction('request_revision')}
                    disabled={actionLoading}
                    className="py-2.5 px-4 rounded-full bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-amber-400 text-xs font-bold font-mono flex items-center justify-center gap-1.5 disabled:opacity-40 transition-all active:scale-[0.98]"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Request Revision</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleReviewAction('reject')}
                    disabled={actionLoading}
                    className="py-2.5 px-4 rounded-full bg-red-950/80 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-bold font-mono flex items-center justify-center gap-1.5 disabled:opacity-40 transition-all active:scale-[0.98]"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                </div>

                {actionSuccessMsg && (
                  <div className="p-2.5 rounded bg-[#102B1E] border border-[#00E599]/40 text-[#00E599] text-xs font-mono flex items-center gap-2">
                    <Check className="w-3.5 h-3.5" />
                    <span>{actionSuccessMsg}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-[#0A1D13] border border-[#1A402D] text-center text-xs text-[#74C69D] font-mono">
              Select a review item from the backlog to view details and record decisions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
