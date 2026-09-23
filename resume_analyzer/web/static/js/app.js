/* Small progressive enhancements. Every page works without this file. */

(function () {
  "use strict";

  // Show the chosen file name in the drop zone.
  var fileInput = document.getElementById("resume");
  var fileLabel = document.querySelector("[data-file-name]");
  if (fileInput && fileLabel) {
    fileInput.addEventListener("change", function () {
      fileLabel.textContent = fileInput.files.length ? fileInput.files[0].name : "No file chosen";
    });
  }

  // Only submit the inputs belonging to the selected category, and show its examples.
  var category = document.getElementById("category");
  var examples = document.querySelector("[data-category-examples]");
  function syncCategory() {
    if (!category) return;
    var selected = category.value;
    document.querySelectorAll(".category-inputs").forEach(function (block) {
      var mine = block.dataset.for === selected;
      block.hidden = !mine;
      block.querySelectorAll("input, select").forEach(function (field) { field.disabled = !mine; });
    });
    if (examples) {
      var option = category.options[category.selectedIndex];
      var list = option && option.dataset.examples;
      examples.textContent = list ? "For example: " + list : "";
    }
  }
  if (category) {
    category.addEventListener("change", syncCategory);
    syncCategory();
  }

  // Tell the user the analysis is running (the embedding model takes a moment).
  var form = document.querySelector(".analyse-form");
  if (form) {
    form.addEventListener("submit", function () {
      var button = form.querySelector("[data-submit-label]");
      if (button) {
        button.disabled = true;
        button.textContent = "Analysing…";
      }
    });
  }

  // "Add another" row in the builder.
  document.querySelectorAll("[data-add-row]").forEach(function (button) {
    button.addEventListener("click", function () {
      var fieldset = button.closest("[data-repeat]");
      var rows = fieldset.querySelector(".rows");
      var template = rows.querySelector("[data-row]");
      var index = parseInt(fieldset.dataset.next, 10) || rows.children.length;
      var clone = template.cloneNode(true);
      clone.querySelectorAll("input, textarea").forEach(function (field) {
        field.value = "";
        field.name = field.name.replace(/__\d+__/, "__" + index + "__");
      });
      rows.appendChild(clone);
      fieldset.dataset.next = index + 1;
    });
  });
})();
