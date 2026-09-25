import {useParams} from "react-router-dom";

function MonitorMetrics(){
    const {monitor_id}=useParams();
    return (
        <p>Monitor metrics for {monitor_id}</p>
    )
}
export default MonitorMetrics
