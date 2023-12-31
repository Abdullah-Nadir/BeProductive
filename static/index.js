// Prevent form submission on pressing Enter key in the task field of both start page and home page
document.getElementById('task').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        if (e.target.classList.contains('start-task')) {
            addStartTask();
        } else {
            addHomeTask();
        }

    }
});


// Function for showing the tasks on the start page
function addStartTask() {
    const taskInput = document.getElementById('task');
    const taskList = document.getElementById('taskList');

    if (taskInput.value !== '') {
        const taskItem = document.createElement('div');
        taskItem.textContent = taskInput.value;
        taskList.appendChild(taskItem);
        taskInput.value = '';

        // Send task to the server
        fetch('/start-task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task: taskItem.textContent })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Task sent to the server:', data);
        })
        .catch(error => {
            console.error('Error sending task to the server:', error);
        });
    }
}


// Function for showing the tasks on the home page
function addHomeTask() {
    const taskInput = document.getElementById('task');
    const taskList = document.getElementById('taskList');

    if (taskInput.value !== '') {
        const div = document.createElement('div');
        div.classList.add('task');
        const span = document.createElement('span');
        span.classList.add('task-text');
        span.textContent = taskInput.value;
        const checkbox = document.createElement('input');
        checkbox.classList.add('task-checkbox');
        checkbox.setAttribute('type', 'checkbox');

        div.appendChild(span);
        div.appendChild(checkbox);

        taskList.appendChild(div);
        taskInput.value = '';

        // Send task to the server
        fetch('/home-task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task: span.textContent })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Task sent to the server:', data);
        })
        .catch(error => {
            console.error('Error sending task to the server:', error);
        });
    }
}


// Functionality for updating the status of tasks both on home page and server
const checkboxes = document.querySelectorAll('.task-checkbox');

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        // Get the task ID associated with the checkbox
        const taskId = this.dataset.taskId;

        // Get the current state (checked/unchecked) of the checkbox
        const isChecked = this.checked;

        // Send a POST request to update the task status
        fetch('/task-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Send the task ID, and checkbox state in the request body
            body: JSON.stringify({
                taskId: taskId,
                isChecked: isChecked
            })
        })
        .then(response => {
            // Check if the response is okay
            if (response.ok) {
                console.log('Task status updated successfully');
            } else {
                throw new Error('Task status update failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

