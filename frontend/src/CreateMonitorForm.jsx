import {useState} from 'react';
export default function CreateMonitorForm() {
  const [monitorName,setMonitorName]=useState("");
  const [monitorUrl,setMonitorUrl]=useState("");
  const [errorMessage, setErrorMessage]=useState("");
  const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
  const [loading,setLoading]=useState(false);
  const [displayMessage,setDisplayMessage]=useState("");
  const [created,setCreated]=useState(false);

  async function handleCreateMonitor(e){
    e.preventDefault();
    setErrorMessage("");
    setDisplayMessage("");
    setLoading(true);
    setCreated(false);
    try {
      const response=await fetch(`${BACKEND_URL}/monitors`,{
        "method":"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify({name:monitorName,url:monitorUrl})
      });

      const result=await response.json();

      if (response.status===409){
        setErrorMessage("A monitor for this URL already exists.");
      }
      else if (response.status===200){
        setDisplayMessage(result.message);
        setCreated(true);
      }
      else{
        setErrorMessage("Something went wrong. Please try again.");
      }
    }
    catch(error){
      setErrorMessage("Unable to connect to the server. Please try again.");
    }
    finally{
      setLoading(false);
    }

  }
  return (
    <>
    {!created && (
      <form onSubmit={handleCreateMonitor}>
        <div className="space-y-12 mt-10">

          <div>
            <h2 className="text-center text-base/7 font-semibold text-gray-900">Create a monitor</h2>
            <p className="text-center mt-1 text-sm/6 text-gray-600">Once created, the URL will be monitored every 5 minutes.</p>

            <div className="mx-auto max-w-xl mt-10 gap-x-6 gap-y-8">
              <div>
                <label htmlFor="monitor-name" className="text-left block text-sm/6 font-medium text-gray-900">
                  Create a name for this monitor
                </label>
                <div className="mt-2">
                  <input
                    id="monitor-name"
                    name="name"
                    type="text"
                    autoComplete="name"
                    onChange={(e)=>setMonitorName(e.target.value)}
                    required
                    className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-green-600 sm:text-sm/6"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="monitor-url" className="text-left mt-2 block text-sm/6 font-medium text-gray-900">
                  Enter URL to monitor
                </label>
                <div className="mt-2">
                  <input
                    id="monitor-url"
                    name="url"
                    type="url"
                    autoComplete="url"
                    onChange={(e)=>setMonitorUrl(e.target.value)}
                    required
                    className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-green-600 sm:text-sm/6"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 flex items-center justify-center gap-x-6">
          <button
            type="submit"
            className="rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-xs hover:bg-green-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
            disabled={loading}
          >
            {loading?"Saving...":"Save"}
          </button>
        </div>
      </form>
    )}
    {/*Error message display */}
    {errorMessage && (<div>
      <p className="mt-1 text-sm/6 text-red-600">{errorMessage}</p>
      </div>
    )
    }
    {/*Success message display */}
    {created && displayMessage && (<div>
    <p className="mt-10 text-center text-2xl text-gray-900">{displayMessage}</p>
    </div>)
    }
    </>
    
  )
}
