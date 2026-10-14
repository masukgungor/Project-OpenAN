// Copyright (c) 2026 Huawei Technologies Co., Ltd.
// All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';
import { createEnergyIntent, getElectricityPrice, classifySite, generateIntentFromDescription } from '@/service/api.js';

export default function IntentForm({ isDark, onIntentCreated, setError }) {
    const [activeTab, setActiveTab] = useState('form');
    const [formData, setFormData] = useState({
        region: 'north',
        energy_target: 'maximized_saving',
        priority: 5,
        cluster_id: '',
        safeguard: {
            min_throughput_mbps: 10,
            max_latency_ms: 50,
            coverage_maintain: true
        },
        validity_period: {
            start: '00:00',
            end: '23:59'
        }
    });

    const [loading, setLoading] = useState(false);
    const [testingPrice, setTestingPrice] = useState(false);
    const [priceData, setPriceData] = useState(null);
    const [testingSite, setTestingSite] = useState(false);
    const [siteResult, setSiteResult] = useState(null);
    const [llmDescription, setLlmDescription] = useState('');
    const [llmLoading, setLlmLoading] = useState(false);
    const [llmRegion, setLlmRegion] = useState('');

    const inputClass = `w-full px-3 py-2 rounded-lg border text-sm ${
        isDark
            ? 'bg-zinc-800 border-zinc-700 text-white'
            : 'bg-white border-zinc-300 text-zinc-900'
    } focus:outline-none focus:ring-2 focus:ring-blue-500`;

    const labelClass = `block text-sm font-medium mb-1 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`;

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleTestPrice = async () => {
        setTestingPrice(true);
        setError(null);
        try {
            const result = await getElectricityPrice(formData.region);
            setPriceData(result);
        } catch (err) {
            setError(`Failed to get electricity price: ${err.message}`);
        } finally {
            setTestingPrice(false);
        }
    };

    const handleTestSite = async () => {
        setTestingSite(true);
        setError(null);
        try {
            const result = await classifySite('SITE-001', 2.5);
            setSiteResult(result);
        } catch (err) {
            setError(`Failed to classify site: ${err.message}`);
        } finally {
            setTestingSite(false);
        }
    };

    const handleGenerateWithLLM = async (e) => {
        e.preventDefault();
        if (!llmDescription.trim()) {
            setError('Please enter a description for the intent');
            return;
        }
        setLlmLoading(true);
        setError(null);
        try {
            console.log('[LLM Intent] Starting generation...');
            const result = await generateIntentFromDescription(llmDescription, llmRegion || null);
            console.log('[LLM Intent] Received result:', result);
            onIntentCreated(result);
            setLlmDescription('');
            setLlmRegion('');
        } catch (err) {
            console.error('[LLM Intent] Error:', err);
            setError(`Failed to generate intent: ${err.message}`);
        } finally {
            setLlmLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const result = await createEnergyIntent(formData);
            onIntentCreated(result);
        } catch (err) {
            setError(`Failed to create intent: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`rounded-lg border p-4 flex flex-col gap-4 h-full overflow-auto ${
            isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
        }`}>
            <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                Create Energy Saving Intent
            </h2>

            <div className="flex border-b border-zinc-700">
                <button
                    type="button"
                    onClick={() => setActiveTab('form')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === 'form'
                            ? 'border-blue-500 text-blue-500'
                            : 'border-transparent text-zinc-500 hover:text-zinc-300'
                    }`}
                >
                    Form
                </button>
                <button
                    type="button"
                    onClick={() => setActiveTab('llm')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === 'llm'
                            ? 'border-blue-500 text-blue-500'
                            : 'border-transparent text-zinc-500 hover:text-zinc-300'
                    }`}
                >
                    Generate with LLM
                </button>
            </div>

            {activeTab === 'llm' ? (
                <form onSubmit={handleGenerateWithLLM} className="flex flex-col gap-3 flex-1">
                    <div>
                        <label className={labelClass}>Description</label>
                        <textarea
                            value={llmDescription}
                            onChange={(e) => setLlmDescription(e.target.value)}
                            placeholder="e.g., I want to maximize energy saving in the north region during off-peak hours while maintaining minimum 10 Mbps throughput"
                            rows={4}
                            className={`w-full px-3 py-2 rounded-lg border text-sm resize-none ${
                                isDark
                                    ? 'bg-zinc-800 border-zinc-700 text-white'
                                    : 'bg-white border-zinc-300 text-zinc-900'
                            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                        />
                    </div>
                    <div>
                        <label className={labelClass}>Preferred Region (optional)</label>
                        <select
                            value={llmRegion}
                            onChange={(e) => setLlmRegion(e.target.value)}
                            className={inputClass}
                        >
                            <option value="">Auto-detect</option>
                            <option value="north">North</option>
                            <option value="south">South</option>
                            <option value="east">East</option>
                            <option value="west">West</option>
                            <option value="central">Central</option>
                        </select>
                    </div>
                    <div className={`p-3 rounded border text-xs ${
                        isDark ? 'bg-zinc-800 border-zinc-700 text-zinc-400' : 'bg-zinc-50 border-zinc-200 text-zinc-600'
                    }`}>
                        The LLM will analyze your description and generate appropriate intent parameters including region, energy target, priority, and safeguard settings.
                    </div>
                    <button
                        type="submit"
                        disabled={llmLoading}
                        className="mt-auto px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {llmLoading ? 'Generating...' : 'Generate Intent'}
                    </button>
                </form>
            ) : (
                <form onSubmit={handleSubmit} className="flex flex-col gap-3 flex-1">
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className={labelClass}>Region</label>
                        <select
                            name="region"
                            value={formData.region}
                            onChange={handleChange}
                            className={inputClass}
                        >
                            <option value="north">North</option>
                            <option value="south">South</option>
                            <option value="east">East</option>
                            <option value="west">West</option>
                            <option value="central">Central</option>
                        </select>
                    </div>

                    <div>
                        <label className={labelClass}>Energy Target</label>
                        <select
                            name="energy_target"
                            value={formData.energy_target}
                            onChange={handleChange}
                            className={inputClass}
                        >
                            <option value="maximized_saving">Maximized Saving</option>
                            <option value="proactive_saving">Proactive Saving</option>
                            <option value="balanced">Balanced</option>
                            <option value="experience_first">Experience First</option>
                        </select>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className={labelClass}>Priority (1-10)</label>
                        <input
                            type="number"
                            name="priority"
                            value={formData.priority}
                            onChange={handleChange}
                            min="1"
                            max="10"
                            className={inputClass}
                        />
                    </div>
                    <div>
                        <label className={labelClass}>Cluster ID (optional)</label>
                        <input
                            type="text"
                            name="cluster_id"
                            value={formData.cluster_id}
                            onChange={handleChange}
                            placeholder="e.g., CLUSTER-NORTH-001"
                            className={inputClass}
                        />
                    </div>
                </div>

                <div className={`text-sm font-medium ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                    Safeguard Settings
                </div>

                <div className="grid grid-cols-3 gap-3 items-end">
                    <div>
                        <label className={labelClass}>Min Throughput (Mbps)</label>
                        <input
                            type="number"
                            name="min_throughput_mbps"
                            value={formData.safeguard.min_throughput_mbps}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                safeguard: { ...prev.safeguard, min_throughput_mbps: parseFloat(e.target.value) }
                            }))}
                            className={inputClass}
                        />
                    </div>
                    <div>
                        <label className={labelClass}>Max Latency (ms)</label>
                        <input
                            type="number"
                            name="max_latency_ms"
                            value={formData.safeguard.max_latency_ms}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                safeguard: { ...prev.safeguard, max_latency_ms: parseFloat(e.target.value) }
                            }))}
                            className={inputClass}
                        />
                    </div>
                    <div className="flex items-center gap-2 pb-1">
                        <input
                            type="checkbox"
                            name="coverage_maintain"
                            checked={formData.safeguard.coverage_maintain}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                safeguard: { ...prev.safeguard, coverage_maintain: e.target.checked }
                            }))}
                            id="coverage_check"
                        />
                        <label htmlFor="coverage_check" className={labelClass + " mb-0 cursor-pointer"}>
                            Maintain Coverage
                        </label>
                    </div>
                </div>

                <div className={`text-sm font-medium ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                    Validity Period
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className={labelClass}>Start Time</label>
                        <input
                            type="time"
                            name="start"
                            value={formData.validity_period.start}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                validity_period: { ...prev.validity_period, start: e.target.value }
                            }))}
                            className={inputClass}
                        />
                    </div>
                    <div>
                        <label className={labelClass}>End Time</label>
                        <input
                            type="time"
                            name="end"
                            value={formData.validity_period.end}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                validity_period: { ...prev.validity_period, end: e.target.value }
                            }))}
                            className={inputClass}
                        />
                    </div>
                </div>

                <div className="flex gap-2 mt-auto pt-4">
                    <button
                        type="submit"
                        disabled={loading}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {loading ? 'Creating...' : 'Create Intent'}
                    </button>
                    <button
                        type="button"
                        onClick={handleTestPrice}
                        disabled={testingPrice}
                        className="px-4 py-2 bg-zinc-600 hover:bg-zinc-700 disabled:bg-zinc-400 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {testingPrice ? 'Testing...' : 'Test Price'}
                    </button>
                    <button
                        type="button"
                        onClick={handleTestSite}
                        disabled={testingSite}
                        className="px-4 py-2 bg-zinc-600 hover:bg-zinc-700 disabled:bg-zinc-400 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {testingSite ? 'Testing...' : 'Test Site'}
                    </button>
                </div>
            </form>
            )}

            <div className="grid grid-cols-2 gap-3 mt-4">
                <div className={`p-3 rounded border text-xs font-mono ${
                    isDark ? 'bg-zinc-800 border-zinc-700 text-zinc-300' : 'bg-zinc-50 border-zinc-200 text-zinc-700'
                }`}>
                    <div className="font-bold mb-1">Electricity Price:</div>
                    {priceData ? (
                        <>
                            <div>Region: {priceData.region}</div>
                            <div>Current Price: {priceData.current_price}</div>
                            <div>Time Slots: {priceData.time_slots?.length || 0}</div>
                            <div>Bands: {priceData.bands?.length || 0}</div>
                        </>
                    ) : (
                        <div className="text-zinc-500">Click "Test Price" to load</div>
                    )}
                </div>
                <div className={`p-3 rounded border text-xs font-mono ${
                    isDark ? 'bg-zinc-800 border-zinc-700 text-zinc-300' : 'bg-zinc-50 border-zinc-200 text-zinc-700'
                }`}>
                    <div className="font-bold mb-1">Site Classification:</div>
                    {siteResult ? (
                        <>
                            <div>Site: {siteResult.site_id}</div>
                            <div>Current Band: {siteResult.current_band}</div>
                            <div>Classified Band: {siteResult.classified_band}</div>
                            <div>Classification: {siteResult.classification}</div>
                            <div>Saving Potential: {siteResult.energy_saving_potential_kw} KW</div>
                        </>
                    ) : (
                        <div className="text-zinc-500">Click "Test Site" to load</div>
                    )}
                </div>
            </div>
        </div>
    );
}
