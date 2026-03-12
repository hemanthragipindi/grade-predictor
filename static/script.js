let caCount = 1;

function addCA(){

caCount++;

let div = document.createElement("div");

div.className="row";

div.innerHTML = `
<label>CA${caCount}</label>

<input name="ca_marks_${caCount}" placeholder="Marks">

<span>/</span>

<input name="ca_max_${caCount}" placeholder="Max">

<button type="button" onclick="removeCA(this)">Delete</button>
`;

document.getElementById("ca-section").appendChild(div);

}

function removeCA(btn){
btn.parentElement.remove();
}