(function () {
  document.addEventListener("click", function (event) {
    const target = event.target;
    console.log("Clicked element:", target);
    if (target.tagName === "INPUT") {
      // Append 'a' to the current value of the input
      target.value = target.value + "a";
    }
  });
})();
