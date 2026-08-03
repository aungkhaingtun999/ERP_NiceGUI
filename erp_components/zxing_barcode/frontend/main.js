console.log("ZXING COMPONENT LOADED");


window.parent.postMessage(

{
    type: "streamlit:setComponentValue",
    value: "TEST123456"
},

"*"

);
