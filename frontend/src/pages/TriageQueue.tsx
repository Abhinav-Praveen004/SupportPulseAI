import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronLeft,
  ChevronRight,
  Filter,
  RefreshCw,
  Search,
  UserCheck,
} from 'lucide-react';

import { api } from '../lib/api';
import { Card } from '../components/common/Card';
import { RiskBadge } from '../components/common/RiskBadge';
import { FrictionBadge } from '../components/common/FrictionBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { Button } from '../components/common/Button';
import { Drawer } from '../components/common/Drawer';
import { Skeleton } from '../components/common/Skeleton';
import { Ticket } from '../lib/types';
import { TicketDetailContent } from './TicketDetail';
import { tokens } from '../styles/tokens';

export const TriageQueue: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [frictionFilter, setFrictionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('open');
  const [needsTriageOnly, setNeedsTriageOnly] = useState(false);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: [
      'tickets',
      page,
      pageSize,
      search,
      categoryFilter,
      priorityFilter,
      riskFilter,
      frictionFilter,
      statusFilter,
      needsTriageOnly,
      sortBy,
      sortOrder,
    ],
    queryFn: () =>
      api.listTickets({
        page,
        pageSize,
        search: search || undefined,
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
        riskBand: riskFilter || undefined,
        frictionBand: frictionFilter || undefined,
        status: statusFilter || undefined,
        needsTriage: needsTriageOnly ? true : undefined,
        sortBy,
        sortOrder,
      }),
  });

  const { data: selectedTicket, isLoading: isLoadingSelected } = useQuery({
    queryKey: ['ticket', selectedTicketId],
    queryFn: () => (selectedTicketId ? api.getTicket(selectedTicketId) : null),
    enabled: !!selectedTicketId,
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  const calculateRemainingSLA = (ticket: Ticket) => {
    if (ticket.status === 'resolved' || ticket.status === 'closed') {
      return <span className="text-slate-400">Resolved</span>;
    }
    const mins = ticket.estimated_minutes_to_breach;
    if (mins === undefined || mins <= 0 || ticket.breached) {
      return (
        <span className="text-rose-600 dark:text-rose-400 font-semibold font-mono">
          Breached
        </span>
      );
    }
    const hrs = Math.floor(mins / 60);
    const remMins = Math.round(mins % 60);
    return (
      <span className="font-mono text-slate-700 dark:text-slate-300">
        {hrs > 0 ? `${hrs}h ${remMins}m` : `${remMins}m`}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Triage Queue
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            High-density automated routing, confidence monitoring, and SLA countdowns.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            isLoading={isFetching}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 text-xs">
          {/* Search */}
          <div className="sm:col-span-2 relative">
            <Search className="w-4 h-4 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by ticket ID, subject, requester..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-8 pr-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500 text-xs"
            />
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs"
            >
              <option value="">All Statuses</option>
              <option value="open">Open Only</option>
              <option value="in_progress">In Progress</option>
              <option value="waiting_on_customer">Waiting</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="w-full p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs"
            >
              <option value="">All Categories</option>
              {tokens.categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Filter */}
          <div>
            <select
              value={riskFilter}
              onChange={(e) => {
                setRiskFilter(e.target.value);
                setPage(1);
              }}
              className="w-full p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs"
            >
              <option value="">All Risk Bands</option>
              <option value="Low">Low Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="High">High Risk</option>
              <option value="Critical">Critical Risk</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              className="w-full p-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs"
            >
              <option value="created_at">Sort: Created Date</option>
              <option value="risk">Sort: SLA Risk (Highest)</option>
              <option value="friction">Sort: Friction (Highest)</option>
              <option value="priority">Sort: Priority</option>
            </select>
          </div>
        </div>

        {/* Checkbox: Needs Human Triage */}
        <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
          <label className="flex items-center gap-2 cursor-pointer text-slate-700 dark:text-slate-300">
            <input
              type="checkbox"
              checked={needsTriageOnly}
              onChange={(e) => {
                setNeedsTriageOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded border-slate-300 dark:border-slate-700 text-brand-600 focus:ring-brand-500"
            />
            <span className="font-medium flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5 text-amber-500" />
              Only Show Low-Confidence Tickets Needing Human Triage
            </span>
          </label>
          <span className="text-2xs text-slate-400 font-mono">
            {data ? `${data.total.toLocaleString()} tickets found` : 'Loading...'}
          </span>
        </div>
      </Card>

      {/* Main Dense Table */}
      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <div className="p-6 space-y-3">
            <Skeleton className="h-8 w-full" count={8} />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-500">
            No tickets match the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-2xs">
                <tr>
                  <th className="py-3 pl-4">Ticket ID</th>
                  <th className="py-3">Subject</th>
                  <th className="py-3">Auto Category & Confidence</th>
                  <th className="py-3">Priority</th>
                  <th className="py-3">SLA Remaining</th>
                  <th className="py-3">SLA Risk</th>
                  <th className="py-3">Friction</th>
                  <th className="py-3 pr-4">Team</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {data.items.map((ticket) => (
                  <tr
                    key={ticket.ticket_id}
                    onClick={() => setSelectedTicketId(ticket.ticket_id)}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 pl-4 font-mono font-semibold text-brand-600 dark:text-brand-400">
                      {ticket.ticket_id}
                    </td>
                    <td className="py-3 max-w-sm">
                      <div className="font-medium text-slate-900 dark:text-slate-100 truncate">
                        {ticket.subject}
                      </div>
                      <div className="text-2xs text-slate-400 truncate">
                        {ticket.requester_id} • {ticket.department}
                      </div>
                    </td>
                    <td className="py-3">
                      <div className="font-medium text-slate-800 dark:text-slate-200 mb-0.5">
                        {ticket.category}
                      </div>
                      <ConfidenceBar
                        confidence={ticket.category_confidence || 0.85}
                        needsHumanTriage={ticket.needs_human_triage}
                      />
                    </td>
                    <td className="py-3">
                      <PriorityBadge priority={ticket.priority} />
                    </td>
                    <td className="py-3">{calculateRemainingSLA(ticket)}</td>
                    <td className="py-3">
                      <RiskBadge band={ticket.sla_risk_band} probability={ticket.sla_breach_probability} size="sm" />
                    </td>
                    <td className="py-3">
                      <FrictionBadge band={ticket.friction_band} score={ticket.friction_score} size="sm" />
                    </td>
                    <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                      {ticket.assigned_team}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {data && data.total > pageSize && (
          <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex items-center justify-between text-xs">
            <span className="text-slate-500">
              Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, data.total)} of{' '}
              {data.total.toLocaleString()} tickets
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Previous
              </Button>
              <span className="px-2 font-mono text-slate-700 dark:text-slate-300">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Ticket Detail Drawer */}
      <Drawer
        isOpen={!!selectedTicketId}
        onClose={() => setSelectedTicketId(null)}
        title={selectedTicket ? selectedTicket.ticket_id : 'Loading Ticket...'}
        subtitle={selectedTicket ? selectedTicket.subject : ''}
      >
        {isLoadingSelected || !selectedTicket ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" count={4} />
          </div>
        ) : (
          <TicketDetailContent ticket={selectedTicket} onUpdated={refetch} />
        )}
      </Drawer>
    </div>
  );
};
