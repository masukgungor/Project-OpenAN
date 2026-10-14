// Copyright (c) 2026 Huawei Technologies Co., Ltd.
// All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0

import { useState, useEffect, useRef } from 'react';
import IntentForm from './intent-form.jsx';
import ResultsPanel from './results-panel.jsx';
import ReferenceInfo from './reference-info.jsx';
import { subscribeToWorkflowExecution } from '@/service/api.js';

const STORAGE_KEY = 'energy_saving_intents';

const STEP_LABELS = {
    'step1': 'Intent Exploration',
    'step2': 'Intent Exploration Request',
    'step3': 'Intent Generation',
    'step4': 'Intent Delivery',
    'step5': 'Lifecycle Management',
    'step6': 'Effect Evaluation'
};

export default function EnergySaving({ isDark }) {
    const [intents, setIntents] = useState([]);
    const [selectedIntent, setSelectedIntent] = useState(null);
    const [error, setError] = useState(null);
    const [running, setRunning] = useState(false);
    const [currentStep, setCurrentStep] = useState(null);
    const [stepHistory, setStepHistory] = useState([]);
    const [negotiationLogs, setNegotiationLogs] = useState([]);
    const [showLogs, setShowLogs] = useState(false);
    const eventSourceRef = useRef(null);

    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setIntents(parsed);
            } catch (e) {
                console.error('Failed to parse stored intents:', e);
            }
        }
    }, []);

    useEffect(() => {
        if (intents.length > 0) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(intents));
        }
    }, [intents]);

    const handleIntentCreated = (intent) => {
        console.log('[handleIntentCreated] New intent:', intent);
        console.log('[handleIntentCreated] source:', intent.source);
        const newIntent = { ...intent, workflow_progress: [], step_history: [] };
        setIntents(prev => {
            const updated = [newIntent, ...prev];
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
            return updated;
        });
        setSelectedIntent(newIntent);
    };

    const formatLogTime = (timeStr) => {
        const date = new Date(timeStr);
        return date.toLocaleTimeString();
    };

    const toggleLogs = () => setShowLogs(!showLogs);

    const handleRunWorkflow = () => {
        if (!selectedIntent) {
            setError('Select an intent first');
            return;
        }
        
        setRunning(true);
        setError(null);
        setCurrentStep(null);
        setStepHistory([]);
        
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }
        
        const currentIntentId = selectedIntent.intent_id;
        const saveIntentsToStorage = (updatedIntents) => {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedIntents));
        };
        
        const updateIntentStatus = (newStatus) => {
            setIntents(prev => {
                const updated = prev.map(i => 
                    i.intent_id === currentIntentId ? { ...i, status: newStatus } : i
                );
                saveIntentsToStorage(updated);
                return updated;
            });
            setSelectedIntent(prev => prev ? { ...prev, status: newStatus } : null);
        };
        
        const eventSource = subscribeToWorkflowExecution(
            currentIntentId,
            'RAN Energy Saving Agent',
            (event) => {
                const evtType = event.type;
                const evtData = event.data || {};
                
                if (evtType === 'step_start') {
                    const stepName = evtData.step;
                    setCurrentStep(stepName);
                    setIntents(prev => {
                        const intent = prev.find(i => i.intent_id === currentIntentId);
                        if (intent && intent.status === 'pending') {
                            const updated = prev.map(i => i.intent_id === currentIntentId ? { ...i, status: 'in_progress' } : i);
                            saveIntentsToStorage(updated);
                            return updated;
                        }
                        return prev;
                    });
                } else if (evtType === 'step_complete') {
                    const stepName = evtData.step;
                    const newHistory = [...stepHistory, { step: stepName, status: 'completed' }];
                    setStepHistory(newHistory);
                    setCurrentStep(null);
                    setIntents(prev => {
                        const updated = prev.map(i => 
                            i.intent_id === currentIntentId ? { ...i, step_history: newHistory } : i
                        );
                        saveIntentsToStorage(updated);
                        return updated;
                    });
                } else if (evtType === 'task_status_changed') {
                    const stepName = evtData.step;
                    const status = evtData.status;
                    setStepHistory(prev => {
                        const existing = prev.find(h => h.step === stepName);
                        if (existing) return prev;
                        const newHistory = [...prev, { step: stepName, status }];
                        setIntents(prev => {
                            const updated = prev.map(i => 
                                i.intent_id === currentIntentId ? { ...i, step_history: newHistory } : i
                            );
                            saveIntentsToStorage(updated);
                            return updated;
                        });
                        return newHistory;
                    });
                } else if (evtType === 'agent_request') {
                    setNegotiationLogs(prev => [...prev, {
                        time: new Date().toLocaleTimeString(),
                        type: 'request',
                        agent: evtData.agent,
                        data: evtData
                    }]);
                } else if (evtType === 'agent_response') {
                    setNegotiationLogs(prev => [...prev, {
                        time: new Date().toLocaleTimeString(),
                        type: 'response',
                        agent: evtData.agent,
                        data: evtData
                    }]);
                } else if (evtType === 'error') {
                    setError(evtData.error || 'Workflow failed');
                    setRunning(false);
                    updateIntentStatus('failed');
                } else if (evtType === 'end' || evtType === 'close') {
                    setRunning(false);
                    setCurrentStep(null);
                    updateIntentStatus('completed');
                }
            },
            (completeEvent) => {
                setRunning(false);
                setCurrentStep(null);
                updateIntentStatus('completed');
            },
            (err) => {
                console.error('[SSE] Connection error:', err);
                setRunning(false);
            }
        );
        
        eventSourceRef.current = eventSource;
    };
    
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return (
        <div className="h-full flex flex-col p-6 overflow-auto">
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                        Energy Saving
                    </h1>
                    <p className={`text-sm mt-1 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                        RAN Energy Saving Intent Management
                    </p>
                </div>
                <button
                    onClick={handleRunWorkflow}
                    disabled={running || !selectedIntent}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg text-sm font-medium transition-colors"
                >
                    {running ? 'Running...' : 'Run Workflow'}
                </button>
            </div>

            {error && (
                <div className="mb-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-500 text-sm">
                    {error}
                </div>
            )}

            {(running || stepHistory.length > 0) && (
                <div className={`mb-4 p-4 rounded-lg border ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
                    <h3 className={`text-sm font-semibold mb-3 ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                        Workflow Progress
                    </h3>
                    <div className="flex items-center gap-2 overflow-x-auto pb-2">
                        {['step1', 'step2', 'step3', 'step4', 'step5', 'step6'].map((step, index) => {
                            const isCompleted = stepHistory.some(h => h.step === step && h.status === 'completed');
                            const isCurrent = currentStep === step;
                            const stepLabel = STEP_LABELS[step] || step;
                            
                            return (
                                <div key={step} className="flex items-center gap-2 flex-shrink-0">
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                        isCompleted 
                                            ? 'bg-green-600 text-white' 
                                            : isCurrent 
                                                ? 'bg-blue-600 text-white animate-pulse' 
                                                : isDark 
                                                    ? 'bg-zinc-800 text-zinc-500' 
                                                    : 'bg-zinc-100 text-zinc-400'
                                    }`}>
                                        {isCompleted ? '✓' : index + 1}
                                    </div>
                                    <div className={`text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                                        {stepLabel}
                                    </div>
                                    {index < 5 && (
                                        <div className={`w-8 h-0.5 ${
                                            isCompleted 
                                                ? 'bg-green-600' 
                                                : isDark 
                                                    ? 'bg-zinc-800' 
                                                    : 'bg-zinc-200'
                                        }`} />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                    {currentStep && (
                        <div className={`mt-2 text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                            Current: {STEP_LABELS[currentStep] || currentStep}...
                        </div>
                    )}
                </div>
            )}

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
                <div className="flex flex-col min-h-0">
                    <IntentForm
                        isDark={isDark}
                        onIntentCreated={handleIntentCreated}
                        setError={setError}
                    />
                </div>
                <div className="flex flex-col min-h-0">
                    <ResultsPanel
                        isDark={isDark}
                        intents={intents}
                        selectedIntent={selectedIntent}
                        onSelectIntent={(intent) => {
                            setSelectedIntent(intent);
                            setStepHistory(intent.step_history || []);
                            setRunning(intent.status === 'in_progress');
                            setCurrentStep(null);
                        }}
                        onDeleteIntent={(intentId) => {
                            setIntents(prev => {
                                const updated = prev.filter(i => i.intent_id !== intentId);
                                localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
                                return updated;
                            });
                            if (selectedIntent?.intent_id === intentId) {
                                setSelectedIntent(null);
                                setStepHistory([]);
                            }
                        }}
                    />
                </div>
                <div className="flex flex-col min-h-0">
                    <ReferenceInfo isDark={isDark} />
                </div>
            </div>

            <div className="fixed bottom-4 right-4 z-50">
                <button
                    onClick={toggleLogs}
                    className={`px-4 py-2 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 ${
                        isDark ? 'bg-zinc-800 border border-zinc-700 text-white' : 'bg-white border border-zinc-200 text-zinc-900'
                    } ${negotiationLogs.length > 0 ? 'ring-2 ring-blue-500' : ''}`}
                >
                    <span>Agent Logs</span>
                    {negotiationLogs.length > 0 && (
                        <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded">{negotiationLogs.length}</span>
                    )}
                    <span className={`transform transition-transform ${showLogs ? 'rotate-180' : ''}`}>▼</span>
                </button>
            </div>

            {showLogs && (
                <div className={`fixed bottom-16 right-4 w-96 max-h-96 rounded-lg border shadow-xl z-50 overflow-hidden flex flex-col ${
                    isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-200'
                }`}>
                    <div className="flex justify-between items-center p-3 border-b border-zinc-700">
                        <h3 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                            Agent Communication Log
                        </h3>
                        <button
                            onClick={() => setNegotiationLogs([])}
                            className={`text-xs px-2 py-1 rounded ${isDark ? 'bg-zinc-700 text-zinc-300' : 'bg-zinc-200 text-zinc-600'}`}
                        >
                            Clear
                        </button>
                    </div>
                    <div className="flex-1 overflow-auto p-2 space-y-2">
                        {negotiationLogs.length === 0 ? (
                            <div className={`text-sm text-center py-8 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                                No agent communication yet.
                            </div>
                        ) : (
                            negotiationLogs.map((log, idx) => (
                                <div key={idx} className={`text-xs p-2 rounded ${
                                    log.type === 'request' 
                                        ? isDark ? 'bg-blue-900/30 border border-blue-800' : 'bg-blue-50 border border-blue-200'
                                        : isDark ? 'bg-green-900/30 border border-green-800' : 'bg-green-50 border border-green-200'
                                }`}>
                                    <div className="flex justify-between mb-1">
                                        <span className={`font-medium ${log.type === 'request' ? 'text-blue-500' : 'text-green-500'}`}>
                                            {log.type === 'request' ? '→' : '←'} {log.agent}
                                        </span>
                                        <span className={isDark ? 'text-zinc-500' : 'text-zinc-400'}>{formatLogTime(log.time)}</span>
                                    </div>
                                    <pre className={`text-xs overflow-auto ${isDark ? 'text-zinc-300' : 'text-zinc-600'}`}>
                                        {JSON.stringify(log.data, null, 2)}
                                    </pre>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
