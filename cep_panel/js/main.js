
(function () {

    "use strict";

    var selectedVideo = null;
    var selectedFormat = "9:16";

    var API = "http://127.0.0.1:8765";

    var selectButton = document.getElementById("selectVideo");
    var analyzeButton = document.getElementById("analyzeButton");

    var videoName = document.getElementById("videoName");
    var engineStatus = document.getElementById("engineStatus");
    var statusMessage = document.getElementById("statusMessage");

    var smoothness = document.getElementById("smoothness");
    var smoothValue = document.getElementById("smoothValue");

    var progressBar = document.getElementById("progressBar");
    var resultMessage = document.getElementById("resultMessage");

    // Select output format
    document.querySelectorAll(".format").forEach(function (button) {

        button.addEventListener("click", function () {

            document.querySelectorAll(".format").forEach(function (item) {
                item.classList.remove("active");
            });

            button.classList.add("active");

            selectedFormat = button.dataset.format;

        });

    });

    // Tracking smoothness
    smoothness.addEventListener("input", function () {

        smoothValue.textContent = smoothness.value + "%";

    });

    // Select video using CEP Node.js
    selectButton.addEventListener("click", function () {

        try {

            var fs = require("fs");
            var path = require("path");

            var dialog = require("electron").remote.dialog;

            dialog.showOpenDialog({
                properties: ["openFile"],
                filters: [
                    {
                        name: "Video",
                        extensions: ["mp4", "mov", "avi"]
                    }
                ]
            }).then(function (result) {

                if (result.canceled || !result.filePaths.length) {
                    return;
                }

                selectedVideo = result.filePaths[0];

                videoName.textContent =
                    path.basename(selectedVideo);

                checkEngine();

            });

        } catch (error) {

            resultMessage.textContent =
                "File selection error: " + error.message;

        }

    });

    // Check Python engine
    function checkEngine() {

        fetch(API + "/health")
            .then(function (response) {

                if (!response.ok) {
                    throw new Error("Engine unavailable");
                }

                return response.json();

            })
            .then(function (data) {

                engineStatus.textContent = "ONLINE";
                engineStatus.className = "status online";

                statusMessage.textContent = data.message;

                analyzeButton.disabled = !selectedVideo;

            })
            .catch(function () {

                engineStatus.textContent = "OFFLINE";
                engineStatus.className = "status offline";

                statusMessage.textContent =
                    "Start the SafeFrame Python Engine.";

                analyzeButton.disabled = true;

            });

    }

    // Analyze and reframe
    analyzeButton.addEventListener("click", function () {

        if (!selectedVideo) {
            return;
        }

        analyzeButton.disabled = true;
        progressBar.style.width = "10%";

        resultMessage.textContent = "Starting AI analysis...";

        fetch(API + "/analyze", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                video_path: selectedVideo,
                format: selectedFormat,
                smoothness: Number(smoothness.value)

            })

        })
        .then(function (response) {

            if (!response.ok) {
                throw new Error("Analysis request failed");
            }

            return response.json();

        })
        .then(function (data) {

            progressBar.style.width = "100%";

            resultMessage.textContent =
                data.message || "Analysis completed.";

        })
        .catch(function (error) {

            resultMessage.textContent =
                "Error: " + error.message;

        })
        .finally(function () {

            analyzeButton.disabled = !selectedVideo;

        });

    });

    checkEngine();

    setInterval(checkEngine, 5000);

})();
