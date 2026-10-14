// Copyright (c) 2026 Huawei Technologies Co., Ltd.
// All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

export default function ResultsPanel({ isDark, intents, selectedIntent, onSelectIntent, onDeleteIntent }) {
    const [viewMode, setViewMode] = useState('details');
    const [showModal, setShowModal] = useState(false);
    const [hoveredId, setHoveredId] = useState(null);

    const borderClass = isDark ? 'border-zinc-800' : 'border-zinc-200';
    const bgClass = isDark ? 'bg-zinc-900' : 'bg-white';
    const textClass = isDark ? 'text-zinc-300' : 'text-zinc-700';
    const headerClass = isDark ? 'text-zinc-400' : 'text-zinc-600';
    const hoverClass = isDark ? 'hover:bg-zinc-800' : 'hover:bg-zinc-50';

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'text-yellow-500';
            case 'approved': return 'text-green-500';
            case 'executed': return 'text-blue-500';
            case 'failed': return 'text-red-500';
            default: return 'text-zinc-500';
        }
    };

    const getSourceBadge = (source) => {
        if (source === 'llm') {
            return <span className="text-xs px-2 py-0.5 rounded bg-purple-600 text-white">LLM</span>;
        }
        return <span className="text-xs px-2 py-0.5 rounded bg-zinc-600 text-white">Form</span>;
    };

    const openModal = () => setShowModal(true);
    const closeModal = () => setShowModal(false);

    return (
        <div className={`rounded-lg border p-4 flex flex-col h-full min-h-0 ${bgClass} ${borderClass}`}>
            <div className="flex justify-between items-center mb-4">
                <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                    Intent History
                </h2>
                {selectedIntent && (
                    <button
                        onClick={openModal}
                        className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                    >
                        View JSON
                    </button>
                )}
            </div>

            <div className="flex-1 overflow-auto min-h-0">
                {intents.length === 0 ? (
                    <div className={`text-center py-8 text-sm ${headerClass}`}>
                        No intents yet. Create one to get started.
                    </div>
                ) : (
                    <div className="space-y-2">
                        {intents.map((intent, index) => (
                            <div
                                key={intent.intent_id || index}
                                onClick={() => onSelectIntent(intent)}
                                onMouseEnter={() => setHoveredId(intent.intent_id)}
                                onMouseLeave={() => setHoveredId(null)}
                                className={`p-3 rounded border cursor-pointer transition-colors ${borderClass} ${hoverClass} ${
                                    selectedIntent?.intent_id === intent.intent_id
                                        ? isDark ? 'border-blue-500 bg-zinc-800' : 'border-blue-500 bg-blue-50'
                                        : ''
                                }`}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <span className={`font-mono text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                                        {intent.intent_id}
                                    </span>
                                    <div className="flex gap-1 items-center">
                                        {getSourceBadge(intent.source)}
                                        <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(intent.status)} ${
                                            isDark ? 'bg-zinc-800' : 'bg-zinc-100'
                                        }`}>
                                            {intent.status}
                                        </span>
                                        {hoveredId === intent.intent_id && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onDeleteIntent && onDeleteIntent(intent.intent_id);
                                                }}
                                                className="text-xs px-2 py-0.5 rounded bg-red-600 hover:bg-red-700 text-white"
                                            >
                                                Delete
                                            </button>
                                        )}
                                    </div>
                                </div>
                                <div className={`text-sm ${textClass}`}>
                                    {intent.region} / {intent.energy_target}
                                </div>
                                <div className={`text-xs mt-1 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                                    {intent.created_at ? new Date(intent.created_at).toLocaleString() : 'No date'}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {selectedIntent && (
                <div className={`mt-4 p-3 rounded border ${borderClass}`}>
                    <h3 className={`text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                        Selected Intent Details
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className={headerClass}>Intent ID:</div>
                        <div className={`font-mono ${textClass}`}>{selectedIntent.intent_id}</div>
                        
                        <div className={headerClass}>Region:</div>
                        <div className={textClass}>{selectedIntent.region}</div>
                        
                        <div className={headerClass}>Target:</div>
                        <div className={textClass}>{selectedIntent.energy_target}</div>
                        
                        <div className={headerClass}>Status:</div>
                        <div className={getStatusColor(selectedIntent.status)}>{selectedIntent.status}</div>
                        
                        <div className={headerClass}>Source:</div>
                        <div>{getSourceBadge(selectedIntent.source)}</div>
                        
                        {selectedIntent.created_at && (
                            <>
                                <div className={headerClass}>Created:</div>
                                <div className={textClass}>{new Date(selectedIntent.created_at).toLocaleString()}</div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {showModal && selectedIntent && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={closeModal}>
                    <div 
                        className={`max-w-2xl w-full max-h-[80vh] rounded-lg border p-4 overflow-auto ${bgClass} ${borderClass}`}
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-center mb-4">
                            <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                                Intent JSON - {selectedIntent.intent_id}
                            </h3>
                            <button
                                onClick={closeModal}
                                className={`px-3 py-1 text-sm rounded ${isDark ? 'bg-zinc-700 text-zinc-300' : 'bg-zinc-200 text-zinc-700'}`}
                            >
                                Close
                            </button>
                        </div>
                        <pre className={`text-xs font-mono p-3 rounded overflow-auto ${isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-50 text-zinc-700'}`}>
                            {JSON.stringify(selectedIntent, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
}
