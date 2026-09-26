import {useParams} from "react-router-dom";
import {useEffect,useState} from 'react';
const ERROR_THRESHOLD=1;
function MonitorMetrics(){
    const {monitor_id}=useParams();
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const [metrics,setMetrics]=useState([]);
    const [errorMessage,setErrorMessage]=useState("");
    async function handleGetMonitorMetrics(){
        setMetrics([]);
        try {
            const response=await fetch(`${BACKEND_URL}/monitors/${monitor_id}`,{
                "method":"GET",
                "headers":{
                    "Content-Type":"application/json"
                }
            });

            const result=await response.json()

            if (response.status!=200){
                setErrorMessage("Something went wrong");
            }
            else if (result.data.length===0){
                setErrorMessage(result.message);
            }
            else {
                setMetrics(result.data);
            }
        }
        catch(e){
            setErrorMessage(`Something went wrong: ${e}`)
        }
        finally{

        }


    }
    useEffect(()=>{
        handleGetMonitorMetrics()
    },[])
    return (
        <>
        {errorMessage && (
            <p className="mt-4 text-red-600">{errorMessage}</p>
        )}
        {/*Metrics Card */}
        {metrics && Object.keys(metrics).length===5 && 
            (
                <div className="mt-4 mx-auto max-w-10/12">
                    <h3 className="text-3xl font-semibold text-gray-900">Monitor metrics for {metrics["monitor_name"]}</h3>
                    <h3 className="text-base font-semibold text-gray-900">
                        <a href={metrics["monitor_url"]} target="_blank" rel="noreferrer">
                            {metrics["monitor_url"]}
                        </a>
                    </h3>
                    <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
                        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">Uptime Percentage</dt>
                            <dd className="mt-1 text-3xl font-semibold tracking-tight text-emerald-600">{metrics["uptime_percentage"].toFixed(2)}%</dd>
                        </div>
                        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">Average Latency</dt>
                            <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">{metrics["average_latency_ms"].toFixed(2)}
                                <span className="text-sm text-gray-500"> ms</span>
                            </dd>
                        </div>
                        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">Error Rate</dt>
                            <dd className={`mt-1 text-3xl font-semibold tracking-tight ${metrics["error_rate"]>ERROR_THRESHOLD?"text-red-600":"text-emerald-600"}`}>{metrics["error_rate"].toFixed(2)}%</dd>
                        </div>
                    </dl>
                    <p className="text-right mt-2 text-sm text-gray-500">Based on past 24 hours data</p>
                </div>
            )
        }
        </>
    )
}
export default MonitorMetrics
