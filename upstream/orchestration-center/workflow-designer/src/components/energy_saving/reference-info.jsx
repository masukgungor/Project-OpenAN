// Copyright (c) 2026 Huawei Technologies Co., Ltd.
// All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

export default function ReferenceInfo({ isDark }) {
    const [activeTab, setActiveTab] = useState('bands');

    const borderClass = isDark ? 'border-zinc-700' : 'border-zinc-300';
    const bgClass = isDark ? 'bg-zinc-800' : 'bg-zinc-50';
    const textClass = isDark ? 'text-zinc-300' : 'text-zinc-700';
    const headerClass = isDark ? 'text-zinc-200' : 'text-zinc-800';

    const bands = [
        { band: 1, powerMin: '0.00', powerMax: '0.99', ghs: 8247.66 },
        { band: 2, powerMin: '1.00', powerMax: '1.99', ghs: 10628.25 },
        { band: 3, powerMin: '2.00', powerMax: '2.99', ghs: 11956.25 },
        { band: 4, powerMin: '3.00', powerMax: '3.99', ghs: 15409.75 },
        { band: 5, powerMin: '4.00', powerMax: '4.99', ghs: 17784.09 },
    ];

    const timePeriods = [
        { period: '23~5', strategy: 'Maximized Saving', target: '-', rateGuarantee: 'No' },
        { period: '6~9', strategy: 'Proactive Saving', target: '10Mbps', rateGuarantee: 'Yes' },
        { period: '10~15', strategy: 'Experience First', target: 'No degrade', rateGuarantee: '-' },
        { period: '16~17', strategy: 'Proactive Saving', target: '10Mbps', rateGuarantee: 'Yes' },
        { period: '18~22', strategy: 'Experience First', target: 'No degrade', rateGuarantee: '-' },
    ];

    return (
        <div className={`rounded-lg border p-4 h-full flex flex-col ${bgClass} ${borderClass}`}>
            <div className="flex gap-2 mb-4">
                <button
                    onClick={() => setActiveTab('bands')}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                        activeTab === 'bands'
                            ? 'bg-blue-600 text-white'
                            : isDark ? 'bg-zinc-700 text-zinc-300' : 'bg-zinc-200 text-zinc-700'
                    }`}
                >
                    Band Classification
                </button>
                <button
                    onClick={() => setActiveTab('time')}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                        activeTab === 'time'
                            ? 'bg-blue-600 text-white'
                            : isDark ? 'bg-zinc-700 text-zinc-300' : 'bg-zinc-200 text-zinc-700'
                    }`}
                >
                    Time-Period Strategy
                </button>
            </div>

            <div className="flex-1 overflow-auto">
                {activeTab === 'bands' && (
                    <table className="w-full text-xs">
                        <thead>
                            <tr className={`border-b ${borderClass}`}>
                                <th className={`py-2 px-2 text-left ${headerClass}`}>Band</th>
                                <th className={`py-2 px-2 text-left ${headerClass}`}>Power Range (KW)</th>
                                <th className={`py-2 px-2 text-right ${headerClass}`}>Total GHS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {bands.map((b) => (
                                <tr key={b.band} className={`border-b ${borderClass}`}>
                                    <td className={`py-2 px-2 ${textClass}`}>
                                        <span className="px-2 py-0.5 bg-blue-600/20 text-blue-400 rounded">
                                            {b.band}
                                        </span>
                                    </td>
                                    <td className={`py-2 px-2 ${textClass}`}>
                                        {b.powerMin} - {b.powerMax}
                                    </td>
                                    <td className={`py-2 px-2 text-right font-mono ${textClass}`}>
                                        {b.ghs.toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {activeTab === 'time' && (
                    <table className="w-full text-xs">
                        <thead>
                            <tr className={`border-b ${borderClass}`}>
                                <th className={`py-2 px-2 text-left ${headerClass}`}>Time Period</th>
                                <th className={`py-2 px-2 text-left ${headerClass}`}>Strategy</th>
                                <th className={`py-2 px-2 text-left ${headerClass}`}>Target</th>
                                <th className={`py-2 px-2 text-center ${headerClass}`}>Rate Guarantee</th>
                            </tr>
                        </thead>
                        <tbody>
                            {timePeriods.map((t) => (
                                <tr key={t.period} className={`border-b ${borderClass}`}>
                                    <td className={`py-2 px-2 font-mono ${textClass}`}>{t.period}</td>
                                    <td className={`py-2 px-2 ${textClass}`}>
                                        {t.strategy === 'Maximized Saving' && (
                                            <span className="text-green-400">{t.strategy}</span>
                                        )}
                                        {t.strategy === 'Proactive Saving' && (
                                            <span className="text-yellow-400">{t.strategy}</span>
                                        )}
                                        {t.strategy === 'Experience First' && (
                                            <span className="text-blue-400">{t.strategy}</span>
                                        )}
                                    </td>
                                    <td className={`py-2 px-2 ${textClass}`}>{t.target}</td>
                                    <td className={`py-2 px-2 text-center ${textClass}`}>
                                        {t.rateGuarantee === 'Yes' && <span className="text-green-500">✓</span>}
                                        {t.rateGuarantee === 'No' && <span className="text-red-500">✗</span>}
                                        {t.rateGuarantee === '-' && <span className="text-zinc-500">-</span>}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
