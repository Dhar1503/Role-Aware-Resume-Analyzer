/* Progressive enhancement only. Every page works, and shows correct numbers,
   with this file blocked - see docs/design-system.md, "No-JavaScript contract". */

(function () {
  "use strict";

  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------------------------------------------------------------- upload

  var fileInput = document.getElementById("resume");
  var dropzone = document.querySelector("[data-dropzone]");
  var fileLabel = document.querySelector("[data-file-name]");
  var idleLabel = fileLabel ? fileLabel.textContent : "";

  function showFile() {
    if (!fileLabel || !fileInput) return;
    var chosen = fileInput.files && fileInput.files.length;
    fileLabel.textContent = chosen ? fileInput.files[0].name : idleLabel;
    if (dropzone) dropzone.classList.toggle("has-file", !!chosen);
  }

  if (fileInput) fileInput.addEventListener("change", showFile);

  if (dropzone && fileInput && window.DataTransfer) {
    ["dragenter", "dragover"].forEach(function (name) {
      dropzone.addEventListener(name, function (event) {
        event.preventDefault();
        dropzone.classList.add("is-over");
      });
    });
    ["dragleave", "drop"].forEach(function (name) {
      dropzone.addEventListener(name, function () { dropzone.classList.remove("is-over"); });
    });
    dropzone.addEventListener("drop", function (event) {
      event.preventDefault();
      if (!event.dataTransfer || !event.dataTransfer.files.length) return;
      fileInput.files = event.dataTransfer.files;
      showFile();
    });
  }

  // ------------------------------------------------------------- category

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

  // Tell the visitor the analysis is running (the embedding model takes a moment).
  var form = document.querySelector(".analyse-form");
  if (form) {
    form.addEventListener("submit", function () {
      var button = form.querySelector("[data-submit-label]");
      if (!button || button.disabled) return;
      button.disabled = true;
      var text = button.querySelector("span");
      if (text) text.textContent = "Analysing…";
    });
  }

  // ------------------------------------------------------- score count-up

  // The server already rendered the final number; this only replays it from 0.
  function countUp(el, index) {
    var target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;
    var duration = 900;
    var delay = index * 90 + 120;
    var started = null;
    el.textContent = "0";
    function frame(now) {
      if (started === null) started = now;
      var progress = Math.min((now - started) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(target * eased);
      if (progress < 1) requestAnimationFrame(frame);
    }
    setTimeout(function () { requestAnimationFrame(frame); }, delay);
  }

  if (!reduceMotion && window.requestAnimationFrame) {
    document.querySelectorAll("[data-count]").forEach(countUp);
  }

  // --------------------------------------------------------- builder rows

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
      var first = clone.querySelector("input, textarea");
      if (first) first.focus();
    });
  });
})();
