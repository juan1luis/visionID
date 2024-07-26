function copyText(id) {
    console.log(id)
    // Get the text from the specified <p> tag
    var text = document.getElementById(id).innerText;
  
    // Create a temporary textarea element to hold the text
    var tempTextArea = document.createElement("textarea");
    tempTextArea.value = text;
  
    // Append the textarea to the document
    document.body.appendChild(tempTextArea);
  
    // Select the text inside the textarea
    tempTextArea.select();
  
    // Execute the copy command
    document.execCommand("copy");
  
    // Remove the temporary textarea
    document.body.removeChild(tempTextArea);
  
    // Alert the user that the text has been copied
  }






  function graphPie (graph_data){

    var data = [{
      values: graph_data.values,
      labels: graph_data.labels,
      
      name: 'Extactitud',
      textinfo: 'none',
      hole: .4,
      type: 'pie',
      marker: {
        colors: graph_data.colors
      },
    }];
    
    var layout = {
      title: 'Elementos Encontrados',
      annotations: [
        {
          font: {
            size: 16
          },
          showarrow: false,
          text: graph_data.percentage + '%',
        }
      ],
      height: 300,
      width: 300,
      showlegend: false,
    };
    
    Plotly.newPlot('graphSectionPie', data, layout);

  };