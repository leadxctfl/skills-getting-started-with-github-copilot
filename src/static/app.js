document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
        `;

        // Participants section (kept separate to safely append list items)
        const participantsWrapper = document.createElement("div");
        participantsWrapper.className = "participants";

        const participantsHeading = document.createElement("h5");
        participantsHeading.textContent = "Participants";
        participantsWrapper.appendChild(participantsHeading);

        const participantsList = document.createElement("ul");
        participantsList.className = "participants-list";

        // Add each participant as a list item with delete icon
        (details.participants || []).forEach((p) => {
          const li = document.createElement("li");
          
          // Email text
          const emailSpan = document.createElement("span");
          emailSpan.textContent = p;
          li.appendChild(emailSpan);
          
          // Delete icon
          const deleteIcon = document.createElement("span");
          deleteIcon.className = "delete-icon";
          deleteIcon.textContent = "✕";
          deleteIcon.title = `Remove ${p} from ${name}`;
          
          // Handle delete click
          deleteIcon.addEventListener("click", async (event) => {
            event.stopPropagation();
            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(name)}/signup/${encodeURIComponent(p)}`,
                { method: "DELETE" }
              );
              
              if (response.ok) {
                // Remove the item from the DOM
                li.remove();
                // If no more participants, show a message
                if (participantsList.children.length === 0) {
                  const emptyMsg = document.createElement("li");
                  emptyMsg.style.fontStyle = "italic";
                  emptyMsg.style.color = "#999";
                  emptyMsg.textContent = "No participants yet";
                  participantsList.appendChild(emptyMsg);
                }
              } else {
                const error = await response.json();
                alert(error.detail || "Failed to unregister participant");
              }
            } catch (error) {
              alert("Error unregistering participant: " + error.message);
              console.error(error);
            }
          });
          
          li.appendChild(deleteIcon);
          participantsList.appendChild(li);
        });
        
        // Show message if no participants
        if ((details.participants || []).length === 0) {
          const emptyMsg = document.createElement("li");
          emptyMsg.style.fontStyle = "italic";
          emptyMsg.style.color = "#999";
          emptyMsg.textContent = "No participants yet";
          participantsList.appendChild(emptyMsg);
        }

        participantsWrapper.appendChild(participantsList);

        activityCard.appendChild(participantsWrapper);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities list to show updated participant count
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
