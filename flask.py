from flask import Flask, render_template_string, request, jsonify, Response, session, redirect, url_for
from functools import wraps
import json
import os
from datetime import datetime

app = Flask(__name__)
# Secret key for session management. Change this to a random string.
app.secret_key = 'your_very_secret_and_random_string_here'

# --- CREDENTIALS ---
# Change these to your desired username and password
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '123456'
# --- END CREDENTIALS ---

# Database files
NUMBERS_DB = "numbers.json"
USERS_DB = "users.json"
DEPOSITS_DB = "deposits.json"

# --- AUTHENTICATION ---
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid."""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- END AUTHENTICATION ---


def load_data(filename, default=None):
    """Load JSON data from file"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else {}
    return default if default is not None else {}

def save_data(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def delete_specific_number(platform, range_id, number_to_delete):
    """Delete specific number from database"""
    numbers_data = load_data(NUMBERS_DB)

    if (platform in numbers_data and
        range_id in numbers_data[platform] and
        number_to_delete in numbers_data[platform][range_id].get('numbers', [])):

        numbers_data[platform][range_id]['numbers'] = [
            num for num in numbers_data[platform][range_id]['numbers']
            if num != number_to_delete
        ]

        if not numbers_data[platform][range_id]['numbers']:
            del numbers_data[platform][range_id]
            if not numbers_data[platform]:
                del numbers_data[platform]

        save_data(NUMBERS_DB, numbers_data)
        return True

    return False

# HTML Template remains the same
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REDSMSBD - Admin Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .header {
            background: #dc2626;
            color: white;
            text-align: center;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .header h1 {
            font-size: 2.8em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            margin-bottom: 8px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .platforms-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .platform-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
            border-left: 4px solid #2563eb;
        }

        .platform-card:hover {
            transform: translateY(-5px);
        }

        .platform-name {
            font-size: 1.4em;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 10px;
        }

        .range-id {
            color: #6b7280;
            font-size: 0.95em;
            margin-bottom: 8px;
        }

        .total-numbers {
            color: #059669;
            font-weight: bold;
            font-size: 1.1em;
        }

        .empty-state {
            background: white;
            padding: 50px;
            text-align: center;
            border-radius: 12px;
            color: #6b7280;
            font-size: 1.1em;
            grid-column: 1 / -1;
        }

        .empty-state .icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }

        .btn {
            padding: 14px 28px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: #2563eb;
            color: white;
        }

        .btn-primary:hover {
            background: #1d4ed8;
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3);
        }

        .btn-danger {
            background: #dc2626;
            color: white;
        }

        .btn-danger:hover {
            background: #b91c1c;
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(220, 38, 38, 0.3);
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
        }

        .modal-large {
            max-width: 700px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #374151;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #d1d5db;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }

        .form-control:focus {
            border-color: #2563eb;
            outline: none;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        textarea.form-control {
            height: 120px;
            resize: vertical;
            font-family: monospace;
        }

        .delete-item {
            display: flex;
            justify-content: between;
            align-items: center;
            background: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #dc2626;
        }

        .delete-info {
            flex: 1;
        }

        .delete-platform {
            font-weight: bold;
            color: #1f2937;
        }

        .delete-range {
            color: #6b7280;
            font-size: 0.9em;
        }

        .delete-count {
            color: #059669;
            font-size: 0.85em;
        }

        .delete-btn {
            background: #dc2626;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }

        .delete-btn:hover {
            background: #b91c1c;
        }

        .api-info {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-top: 30px;
        }

        .number-information {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-top: 30px;
        }

        .api-endpoint {
            background: #f8fafc;
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            font-family: monospace;
            border-left: 3px solid #2563eb;
        }

        @media (max-width: 768px) {
            .platforms-grid {
                grid-template-columns: 1fr;
            }

            .action-buttons {
                flex-direction: column;
            }

            .btn {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1>REDSMSBD</h1>
        <p>Premium OTP Service Management</p>
    </div>

    <!-- Platforms Grid -->
    <div class="platforms-grid" id="platformsContainer">
        <!-- Platforms will be loaded here dynamically -->
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
        <button class="btn btn-primary" onclick="openAddModal()">
            ➕ ADD NUMBER
        </button>
        <button class="btn btn-danger" onclick="openDeleteModal()">
            🗑️ DELETE NUMBER
        </button>
    </div>

    <!-- NUMBER INFORMATION -->
    <div class="number-information">
        <h3 style="margin-bottom: 15px; color: #1f2937;">☎️ Some Number Information:</h3>
        <div class="api-endpoint">
            <strong>☎️</strong> "672": {"name": "Antarctica", "flag": "🇦🇶"}
        </div>
        <div class="api-endpoint">
            <strong>☎️</strong> "672": {"name": "Norfolk Island", "flag": "🇳🇫"}
        </div>
        <div class="api-endpoint">
            <strong>☎️</strong> "1": {"name": "Canada", "flag": "🇨🇦"}
        </div>
        <div class="api-endpoint">
            <strong>☎️</strong> "1": {"name": "United States", "flag": "🇺🇸"}
        </div>
        <div class="api-endpoint">
            <strong>☎️</strong> "7": {"name": "Kazakhstan", "flag": "🇰🇿"}
        </div>
        <div class="api-endpoint">
            <strong>☎️</strong> "7": {"name": "Russia", "flag": "🇷🇺"}
        </div>
        <div class="api-endpoint">
            <strong>GET</strong> /api/platforms - Get all platforms
        </div>
        <div class="api-endpoint">
            <strong>GET</strong> /api/ranges/&lt;platform&gt; - Get ranges for platform
        </div>
        <div class="api-endpoint">
            <strong>GET</strong> /api/get_number/&lt;platform&gt;/&lt;range_id&gt; - Get a number (auto-deletes from DB)
        </div>
        <div class="api-endpoint">
            <strong>POST</strong> /api/delete_number - Delete specific number (for OTP not received)
        </div>
        <div class="api-endpoint">
            <strong>GET</strong> /api/test - Test API connection
        </div>
        <div class="api-endpoint">
            <strong>GET</strong> /api/users - Get all users
        </div>
        <div class="api-endpoint">
            <strong>POST</strong> /api/users - Save all users
        </div>
        <div class="api-endpoint">
            <strong>GET</strong> /api/deposits - Get all deposits
        </div>
        <div class="api-endpoint">
            <strong>POST</strong> /api/deposits - Save all deposits
        </div>
    </div>

    <!-- Add Number Modal -->
    <div id="addModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px; color: #1f2937; font-size: 1.5em;">Add New Numbers</h2>
            <form id="addForm">
                <div class="form-group">
                    <label for="platform">Platform:</label>
                    <select class="form-control" id="platform" name="platform" required>
                        <option value="">Select Platform</option>
                        <option value="Facebook">Facebook</option>
                        <option value="WhatsApp">WhatsApp</option>
                        <option value="Telegram">Telegram</option>
                        <option value="Google">Google</option>
                        <option value="Instagram">Instagram</option>
                        <option value="Twitter">Twitter</option>
                        <option value="Other">Other</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="range_id">Range ID:</label>
                    <input type="text" class="form-control" id="range_id" name="range_id"
                           placeholder="e.g., BANGLADESH 1234" required>
                </div>

                <div class="form-group">
                    <label for="numbers">Numbers (one per line):</label>
                    <textarea class="form-control" id="numbers" name="numbers"
                              placeholder="162628272&#10;163629292&#10;1003627182" required></textarea>
                </div>

                <div style="display: flex; gap: 10px;">
                    <button type="submit" class="btn btn-primary" style="flex: 1;">💾 SAVE</button>
                    <button type="button" class="btn btn-danger" style="flex: 1;"
                            onclick="closeAddModal()">❌ CANCEL</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Delete Number Modal -->
    <div id="deleteModal" class="modal">
        <div class="modal-content modal-large">
            <h2 style="margin-bottom: 20px; color: #1f2937; font-size: 1.5em;">Delete Number Range</h2>
            <div id="deleteOptions">
                <!-- Delete options will be loaded here -->
            </div>
            <div style="margin-top: 20px;">
                <button class="btn btn-danger" onclick="closeDeleteModal()" style="width: 100%;">❌ CLOSE</button>
            </div>
        </div>
    </div>

    <script>
        // Load platforms on page load
        document.addEventListener('DOMContentLoaded', loadPlatforms);

        async function loadPlatforms() {
            try {
                const response = await fetch('/api/ranges_list');
                const data = await response.json();

                const container = document.getElementById('platformsContainer');

                if (!data.success || data.ranges.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">📭</div>
                            <h3>No numbers added yet</h3>
                            <p>Click "ADD NUMBER" to get started!</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = data.ranges.map(range => `
                    <div class="platform-card">
                        <div class="platform-name">${range.platform}</div>
                        <div class="range-id">${range.range_id}</div>
                        <div class="total-numbers">📊 Total Numbers: ${range.total_numbers}</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading platforms:', error);
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">❌</div>
                        <h3>Error loading platforms</h3>
                        <p>Please try refreshing the page</p>
                    </div>
                `;
            }
        }

        function openAddModal() {
            document.getElementById('addModal').style.display = 'flex';
        }

        function closeAddModal() {
            document.getElementById('addModal').style.display = 'none';
        }

        async function openDeleteModal() {
            try {
                const response = await fetch('/api/ranges_list');
                const data = await response.json();

                const container = document.getElementById('deleteOptions');

                if (!data.success || data.ranges.length === 0) {
                    container.innerHTML = '<p style="text-align: center; color: #6b7280; padding: 20px;">No ranges available to delete.</p>';
                } else {
                    container.innerHTML = data.ranges.map(range => `
                        <div class="delete-item">
                            <div class="delete-info">
                                <div class="delete-platform">${range.platform}</div>
                                <div class="delete-range">${range.range_id}</div>
                                <div class="delete-count">${range.total_numbers} numbers</div>
                            </div>
                            <button class="delete-btn" onclick="deleteRange('${range.platform}', '${range.range_id}')">
                                DELETE
                            </button>
                        </div>
                    `).join('');
                }

                document.getElementById('deleteModal').style.display = 'flex';
            } catch (error) {
                console.error('Error loading delete options:', error);
                document.getElementById('deleteOptions').innerHTML = '<p style="text-align: center; color: #dc2626; padding: 20px;">Error loading ranges</p>';
            }
        }

        function closeDeleteModal() {
            document.getElementById('deleteModal').style.display = 'none';
        }

        async function deleteRange(platform, rangeId) {
            if (!confirm(`Are you sure you want to delete "${platform} - ${rangeId}"? This action cannot be undone.`)) {
                return;
            }

            try {
                const formData = new FormData();
                formData.append('platform', platform);
                formData.append('range_id', rangeId);

                const response = await fetch('/delete_number', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    alert('✅ Range deleted successfully!');
                    closeDeleteModal();
                    await loadPlatforms();
                } else {
                    alert('❌ Error: ' + result.message);
                }
            } catch (error) {
                console.error('Error deleting range:', error);
                alert('❌ Error deleting range. Please try again.');
            }
        }

        // Handle form submission
        document.getElementById('addForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);

            try {
                const response = await fetch('/add_number', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    alert('✅ ' + result.message);
                    closeAddModal();
                    await loadPlatforms();
                    this.reset();
                } else {
                    alert('❌ ' + result.message);
                }
            } catch (error) {
                console.error('Error adding numbers:', error);
                alert('❌ Error adding numbers. Please try again.');
            }
        });

        // Close modals when clicking outside
        window.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });

        // Close modals with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeAddModal();
                closeDeleteModal();
            }
        });
    </script>
</body>
</html>
'''

# --- SECURED FLASK ROUTES ---
# The main dashboard is now protected
@app.route('/')
@requires_auth
def dashboard():
    """Main dashboard showing platforms and numbers"""
    return render_template_string(HTML_TEMPLATE)

# These form-handling routes are also protected
@app.route('/add_number', methods=['POST'])
@requires_auth
def add_number():
    """Add numbers to database"""
    platform = request.form.get('platform')
    range_id = request.form.get('range_id')
    numbers_text = request.form.get('numbers')

    if not all([platform, range_id, numbers_text]):
        return jsonify({'success': False, 'message': 'All fields are required'})

    numbers_list = [num.strip() for num in numbers_text.split('\n') if num.strip()]
    numbers_data = load_data(NUMBERS_DB)

    if platform not in numbers_data:
        numbers_data[platform] = {}

    numbers_data[platform][range_id] = {
        'numbers': numbers_list,
        'added_date': datetime.now().isoformat(),
        'total_added': len(numbers_list)
    }

    save_data(NUMBERS_DB, numbers_data)
    return jsonify({'success': True, 'message': f'Added {len(numbers_list)} numbers successfully'})

@app.route('/delete_number', methods=['POST'])
@requires_auth
def delete_number():
    """Delete number range from database"""
    platform = request.form.get('platform')
    range_id = request.form.get('range_id')
    numbers_data = load_data(NUMBERS_DB)

    if platform in numbers_data and range_id in numbers_data[platform]:
        del numbers_data[platform][range_id]
        if not numbers_data[platform]:
            del numbers_data[platform]
        save_data(NUMBERS_DB, numbers_data)
        return jsonify({'success': True, 'message': 'Range deleted successfully'})

    return jsonify({'success': False, 'message': 'Range not found'})

# This helper for the delete modal is also protected
@app.route('/api/ranges_list')
@requires_auth
def get_all_ranges():
    """Get all ranges for delete modal"""
    numbers_data = load_data(NUMBERS_DB)
    ranges_list = []
    for platform, ranges in numbers_data.items():
        for range_id, data in ranges.items():
            ranges_list.append({
                'platform': platform,
                'range_id': range_id,
                'total_numbers': len(data.get('numbers', []))
            })
    return jsonify({'success': True, 'ranges': ranges_list})


# --- PUBLIC API ROUTES (FOR YOUR BOT) ---
# These routes are NOT protected by a password and are accessible by your bot.
@app.route('/api/test')
def test_api():
    """Test API connection"""
    return jsonify({'status': 'ok', 'message': 'Flask API is running', 'timestamp': datetime.now().isoformat()})

@app.route('/api/platforms')
def get_platforms():
    """API endpoint to get all platforms (for bot)"""
    numbers_data = load_data(NUMBERS_DB)
    platforms = list(numbers_data.keys())
    return jsonify({'success': True, 'platforms': platforms})

@app.route('/api/ranges/<platform>')
def get_ranges(platform):
    """API endpoint to get ranges for a platform (for bot)"""
    numbers_data = load_data(NUMBERS_DB)
    if platform in numbers_data:
        ranges = list(numbers_data[platform].keys())
        return jsonify({'success': True, 'ranges': ranges})
    return jsonify({'success': False, 'message': 'Platform not found'})

@app.route('/api/get_number/<platform>/<range_id>')
def get_number(platform, range_id):
    """API endpoint to get a random number (for bot) - AUTO DELETES NUMBER"""
    numbers_data = load_data(NUMBERS_DB)
    if platform in numbers_data and range_id in numbers_data[platform]:
        numbers = numbers_data[platform][range_id].get('numbers', [])
        if numbers:
            number = numbers.pop(0)
            numbers_data[platform][range_id]['numbers'] = numbers
            if not numbers_data[platform][range_id]['numbers']:
                del numbers_data[platform][range_id]
                if not numbers_data[platform]:
                    del numbers_data[platform]
            save_data(NUMBERS_DB, numbers_data)
            return jsonify({
                'success': True,
                'number': number,
                'message': 'Number retrieved and deleted from database'
            })
    return jsonify({'success': False, 'message': 'No numbers available'})

@app.route('/api/delete_number', methods=['POST'])
def api_delete_specific_number():
    """API endpoint to delete specific number (for OTP not received)"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request must be JSON'})
        
    platform = data.get('platform')
    range_id = data.get('range_id')
    number = data.get('number')

    if not all([platform, range_id, number]):
        return jsonify({'success': False, 'message': 'Platform, range_id and number are required'})

    success = delete_specific_number(platform, range_id, number)

    if success:
        return jsonify({'success': True, 'message': 'Number deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Number not found or already deleted'})

# --- New PUBLIC API Endpoints for Users & Deposits ---
@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users data"""
    try:
        users_data = load_data(USERS_DB, {})
        return jsonify({'success': True, 'users': users_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def api_save_users():
    """Save users data"""
    try:
        data = request.get_json()
        if not data or 'users' not in data:
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400
        
        save_data(USERS_DB, data['users'])
        return jsonify({'success': True, 'message': 'Users saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/deposits', methods=['GET'])
def api_get_deposits():
    """Get all deposits data"""
    try:
        deposits_data = load_data(DEPOSITS_DB, [])
        return jsonify({'success': True, 'deposits': deposits_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/deposits', methods=['POST'])
def api_save_deposits():
    """Save deposits data"""
    try:
        data = request.get_json()
        if not data or 'deposits' not in data:
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400
        
        save_data(DEPOSITS_DB, data['deposits'])
        return jsonify({'success': True, 'message': 'Deposits saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # For Replit, you need to specify host='0.0.0.0'
    app.run(host='0.0.0.0', port=8080)

