import React, { useEffect, useState } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Tooltip,
    Legend
} from "chart.js";

import { Doughnut, Line, Bar } from "react-chartjs-2";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Tooltip,
    Legend
);

const API = "http://127.0.0.1:8000";

export default function RiskAnalysis() {

    const [history, setHistory] = useState([]);
    const [riskHistory, setRiskHistory] = useState([]);
    const [prediction, setPrediction] = useState(null);

    async function load() {
    try {

        const [h, rh, p] = await Promise.all([
            fetch(`${API}/history`).then(r => r.json()),
            fetch(`${API}/risk-history`).then(r => r.json()),
            fetch(`${API}/predict`).then(r => r.json())
        ]);

        console.log("history:", h);
        console.log("risk-history:", rh);
        console.log("prediction:", p);

        setHistory(h.metrics || []);
        setRiskHistory(Array.isArray(rh) ? rh : []);
        setPrediction(p);

    } catch (err) {
        console.log(err);
    }
}

    useEffect(() => {

        load();

        const timer = setInterval(load, 5000);

        return () => clearInterval(timer);

    }, []);

    if (!prediction)
        return <h2>Loading...</h2>;

    const risk = prediction.risk_score * 100;

    const latest = history.length
        ? history[history.length - 1]
        : {};

    const cpu = latest.cpu_percent || 0;
    const mem = latest.memory_percent || 0;
    const disk = latest.disk_write_mbps || 0;

    const labels = Array.isArray(riskHistory)
    ? riskHistory.slice(-30).map(x => x.timestamp)
    : [];


const riskValues = Array.isArray(riskHistory)
    ? riskHistory.slice(-30).map(x => x.risk_score * 100)
    : [];

    return (

        <div>

            <h2 style={{ marginBottom: 20 }}>
                Risk Analysis
            </h2>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns: "340px 1fr",
                    gap: 20
                }}
            >

                <div className="card">

                    <h3>Current Risk</h3>

                    <Doughnut
                        data={{
                        labels:["Risk","Remaining"],
                        datasets:[
                            {
                                data:[
                                    risk,
                                    100-risk
                                ],
                                backgroundColor:[
                                    "#ef4444",
                                    "#ced4dd"
                                ],
                                borderColor:[
                                    "#ef4444",
                                    "#c6cdd6"
                                ],
                                borderWidth:2
                            }]
                        }}
                        options={{
                            plugins:{
                                legend:{
                                    labels:{
                                        color:"#cbd5e1"
                                    }
                                }
                            }
                        }}
                    />
                </div>

                <div className="card">

                    <h3>
                        Risk Contribution
                    </h3>

                    <Bar
                    data={{
                        labels:[
                            "CPU",
                            "Memory",
                            "Disk",
                            "Other"
                        ],
                        datasets:[{
                            label:"Contribution",
                                data:[
                                    cpu,
                                    mem,
                                    Math.min(disk*5,100),
                                    Math.max(100-((cpu+mem)/2),0)
                                ],
                                backgroundColor:[
                                     "#103d85",
                                     "#f59e0b",
                                     "#ef4444",
                                     "#8b5cf6"
                                ],
                                borderRadius:8
                         }]
                    }}
                    options={{
                        plugins:{
                            legend:{
                                labels:{
                                    color:"#cbd5e1"
                                }
                            }
                        },
                        scales:{
                            x:{
                                ticks:{
                                    color:"#bea7a7"
                                },
                                grid:{
                                    color:"#0a295b"
                                }
                            }
                        },
                        y:{
                            ticks:{
                                color:"#94a3b8"
                            },
                            grid:{
                                color:"#1e293b"
                            }   
                        },
                        beginAtZero:true,
                        max:100
                    }}
                />

                </div>

            </div>

            <div
                className="card"
                style={{
                    marginTop: 20
                }}
            >

                <h3>
                    Risk Score History
                </h3>

                <Line
                    data={{
                        labels,
                        datasets:[{
                            label:"Risk Score %",
                            data:riskValues,
                            borderColor:"#ef4444",
                            backgroundColor:"rgba(239,68,68,0.2)",
                            pointBackgroundColor:"#ef4444",
                            pointRadius:4,
                            fill:true,
                            tension:0.4
                        }]
                    }}
                    options={{
                        plugins:{
                            legend:{
                                labels:{
                                    color:"#cbd5e1"
                                }
                            }
                        },
                        scales:{
                            x:{
                                ticks:{
                                    color:"#94a3b8"
                                },
                                grid:{
                                    color:"#1e293b"
                                }
                            }
                        },
                        y:{
                            ticks:{
                                color:"#94a3b8"
                            },
                            grid:{
                                color:"#1e293b"
                            }
                        },
                        min:0,
                        max:100
                    }
                }
            />
            </div>
        </div>

    );

}