// API Configuration
const API = {
    base: "https://prompt.harshiitkgp.in/api",
    search: '/prompts/search',
    categories: '/categories',
    customize: '/prompts/customize',
    upload: '/create_prompt',
    like: '/prompts/:prompt_id/like',
    author: '/prompts/author/:author_id'
};

function debugElement(id) {
    const element = document.getElementById(id);
    console.log(`Element ${id}:`, element);
    return element;
}

// Helper function for API calls
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API.base}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// State Management
let currentPage = 1;
const pageSize = 9;
let currentCategory = null;
let currentSearchQuery = '';

// DOM Elements
const searchContainer = document.getElementById('search-container');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const resultsContainer = document.getElementById('results-container');
const resultsGrid = document.getElementById('results-grid');
const promptModal = document.getElementById('prompt-modal');
const shareModal = document.getElementById('share-modal');
const categoriesContainer = document.getElementById('categories-container');
const paginationContainer = document.getElementById('pagination-container');
const titleSection = document.querySelector('.mb-8'); // Logo/title section

// Initialize
window.onload = function() {
    initializeCategories();
    initializeClipboard();
    checkUrlForPrompt();
    
    // Add click event to logo/title
    titleSection.style.cursor = 'pointer';
    titleSection.addEventListener('click', resetToHome);
};

// Initialize Categories
async function initializeCategories() {
    try {
        const categories = await fetchAPI(API.categories);
        
        categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'px-4 py-2 text-sm text-white bg-zinc-900 rounded-full hover:bg-zinc-800 focus:outline-none';
            button.textContent = category;
            button.addEventListener('click', () => searchByCategory(category));
            categoriesContainer.appendChild(button);
        });
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Initialize Clipboard.js
function initializeClipboard() {
    const clipboard = new ClipboardJS('#copy-button', {
        text: () => document.getElementById('modal-prompt').textContent
    });

    clipboard.on('success', () => {
        const copyButton = document.getElementById('copy-button');
        copyButton.textContent = 'Copied!';
        setTimeout(() => copyButton.textContent = 'Copy Prompt', 2000);
    });
}

// Search Functions
async function performSearch() {
    const query = searchInput.value.trim();

    currentSearchQuery = query;
    currentCategory = null;
    currentPage = 1;
    
    document.getElementById('categories-section').style.display = 'none';
    searchContainer.classList.remove('justify-center');
    searchContainer.classList.add('pt-8');
    resultsContainer.classList.remove('hidden');
    
    try {
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Searching...</div>';
        
        const searchParams = new URLSearchParams({
            query: query || undefined,
            page: currentPage,
            page_size: pageSize,
            sort_by: 'created_at',
            sort_order: 'desc'
        });

        if (currentCategory) {
            searchParams.append('category', currentCategory);
        }

        const results = await fetchAPI(`${API.search}?${searchParams}`);
        
        if (results.items.length === 0) {
            resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">No results found</div>';
        } else {
            displayResults(results);
        }
    } catch (error) {
        console.error('Search error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred while searching</div>';
    }
}

async function searchByCategory(category) {
    currentCategory = category;
    currentSearchQuery = '';
    currentPage = 1;
    searchInput.value = '';
    
    document.getElementById('categories-section').style.display = 'none';
    searchContainer.classList.remove('justify-center');
    searchContainer.classList.add('pt-8');
    resultsContainer.classList.remove('hidden');

    try {
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Loading...</div>';
        
        const searchParams = new URLSearchParams({
            category: category,
            page: currentPage,
            page_size: pageSize
        });

        const results = await fetchAPI(`${API.search}?${searchParams}`);
        
        if (results.items.length === 0) {
            resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">No prompts found in this category</div>';
        } else {
            displayResults(results);
        }
    } catch (error) {
        console.error('Category search error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred</div>';
    }
}

// Like functionality
async function likePrompt(promptId) {
    try {
        const response = await fetchAPI(`/prompts/${promptId}/like`, {
            method: 'POST'
        });
        
        if (response.success) {
            const loveButton = document.getElementById('love-button');
            const loveCount = document.getElementById('love-count');
            
            // Get current count and increment it
            let currentCount = parseInt(loveCount.textContent || '0');
            currentCount += 1;
            
            // Update the display
            loveCount.textContent = currentCount;
            
            // Update the heart icon
            const heartIcon = loveButton.querySelector('i');
            heartIcon.classList.remove('far');
            heartIcon.classList.add('fas');
            
            // Disable the button
            loveButton.disabled = true;
            loveButton.classList.add('opacity-50');
            
            // Optional: Add a success animation
            loveCount.classList.add('scale-110', 'text-red-500');
            setTimeout(() => {
                loveCount.classList.remove('scale-110', 'text-red-500');
            }, 300);
        }
    } catch (error) {
        console.error('Error liking prompt:', error);
        alert('Failed to like prompt: ' + (error.response?.message || 'Prompt Already Liked'));
    }
}

// Upload prompt functionality
async function handleUploadSubmit(event) {
    event.preventDefault();
    const form = event.target;
    
    const promptData = {
        name: form.querySelector('input[placeholder="Prompt Title"]').value,
        description: form.querySelector('textarea[placeholder="Prompt Description"]').value,
        category: form.querySelector('select').value,
        prompt: form.querySelector('textarea[placeholder="Prompt Content"]').value,
        author_id: form.querySelector('textarea[placeholder="Author ID"]').value,
        tags: form.querySelector('input[name="tags"]').value.split(',').map(tag => tag.trim())
    };

    try {
        const response = await fetchAPI(API.upload, {
            method: 'POST',
            body: JSON.stringify(promptData)
        });

        alert(response.message);
        closeUploadModal();
        form.reset();
    } catch (error) {
        console.error('Error uploading prompt:', error);
        alert('Failed to upload prompt');
    }
}

async function customizePrompt(promptId, customization) {
    try {
        const response = await fetchAPI(API.customize, {
            method: 'POST',
            body: JSON.stringify({
                prompt_id: promptId,
                customization_message: customization
            })
        });

        if (response && response.customized_prompt) {
            return response.customized_prompt;
        } else {
            throw new Error('Invalid response from customization API');
        }
    } catch (error) {
        console.error('Customization error:', error);
        throw error;
    }
}

// Handle Page Change
async function handlePageChange(page) {
    currentPage = page;
    
    try {
        const searchParams = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            sort_by: 'created_at',
            sort_order: 'desc'
        });

        if (currentSearchQuery) {
            searchParams.append('query', currentSearchQuery);
        }
        if (currentCategory) {
            searchParams.append('category', currentCategory);
        }

        const results = await fetchAPI(`${API.search}?${searchParams}`);
        displayResults(results);
        window.scrollTo(0, 0);
    } catch (error) {
        console.error('Page change error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred</div>';
    }
}

// Display Functions
function displayResults(results) {
    resultsGrid.innerHTML = '';
    
    results.items.forEach(prompt => {
        const card = document.createElement('div');
        card.className = 'bg-zinc-900 rounded-lg p-6 cursor-pointer hover:bg-zinc-800 transition-colors';
        card.innerHTML = `
            <h3 class="text-xl font-semibold text-white mb-2">${prompt.name}</h3>
            <p class="text-gray-400 mb-2">${prompt.description}</p>
            <div class="flex flex-wrap gap-2">
                <span class="inline-block px-3 py-1 text-sm text-white bg-zinc-800 rounded-full">${prompt.category}</span>
            </div>
        `;
        card.addEventListener('click', () => openModal(prompt));
        resultsGrid.appendChild(card);
    });

    if (results.total_pages > 1) {
        displayPagination(results.total_pages);
    } else {
        paginationContainer.innerHTML = '';
    }
}
// This line need to be added after categories for tags
// ${prompt.tags.map(tag => 
//     `<span class="inline-block px-3 py-1 text-sm text-white bg-zinc-800 rounded-full">${tag}</span>`
// ).join('')}

function displayPagination(totalPages) {
    paginationContainer.innerHTML = '';
    
    const paginationWrapper = document.createElement('div');
    paginationWrapper.className = 'flex justify-center items-center space-x-2 mt-8';
    
    // Previous button
    if (currentPage > 1) {
        const prevButton = createPaginationButton('Previous', currentPage - 1);
        paginationWrapper.appendChild(prevButton);
    }

    // Page numbers
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        paginationWrapper.appendChild(createPaginationButton('1', 1));
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'text-white px-2';
            ellipsis.textContent = '...';
            paginationWrapper.appendChild(ellipsis);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        paginationWrapper.appendChild(createPaginationButton(i.toString(), i, i === currentPage));
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'text-white px-2';
            ellipsis.textContent = '...';
            paginationWrapper.appendChild(ellipsis);
        }
        paginationWrapper.appendChild(createPaginationButton(totalPages.toString(), totalPages));
    }

    // Next button
    if (currentPage < totalPages) {
        const nextButton = createPaginationButton('Next', currentPage + 1);
        paginationWrapper.appendChild(nextButton);
    }

    paginationContainer.appendChild(paginationWrapper);
}

function createPaginationButton(text, page, isActive = false) {
    const button = document.createElement('button');
    button.className = `px-4 py-2 text-sm rounded-lg ${
        isActive 
            ? 'bg-white text-black' 
            : 'bg-zinc-900 text-white hover:bg-zinc-800'
    }`;
    button.textContent = text;
    button.addEventListener('click', () => handlePageChange(page));
    return button;
}

async function checkUrlForPrompt() {
    const urlParams = new URLSearchParams(window.location.search);
    const promptId = urlParams.get('prompt_id');
    
    if (promptId) {
        try {
            const prompt = await fetchPromptById(promptId);
            if (prompt) {
                openModal(prompt);
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
        }
    }
}

// Add this new function for "View All Prompts"
async function viewAllPrompts() {
    currentCategory = null;
    currentSearchQuery = '';
    currentPage = 1;
    searchInput.value = '';
    
    document.getElementById('categories-section').style.display = 'none';
    searchContainer.classList.remove('justify-center');
    searchContainer.classList.add('pt-8');
    resultsContainer.classList.remove('hidden');

    try {
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Loading...</div>';
        
        const searchParams = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            sort_by: 'created_at',
            sort_order: 'desc'
        });

        const results = await fetchAPI(`${API.search}?${searchParams}`);
        displayResults(results);
    } catch (error) {
        console.error('View all prompts error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred</div>';
    }
}

async function fetchPromptById(promptId) {
    try {
        const response = await fetchAPI(`/prompts/${promptId}`);
        return response;
    } catch (error) {
        console.error('Error fetching prompt:', error);
        return null;
    }
}

async function fetchAuthorPrompts(authorId) {
    try {
        const response = await fetchAPI(API.author.replace(':author_id', authorId));
        displayResults(response);
    } catch (error) {
        console.error('Error fetching author prompts:', error);
        showError('Failed to load your prompts');
    }
}

function openAuthorPromptsModal() {
    const authorId = prompt('Please enter your Author ID:');
    if (authorId) {
        fetchAuthorPrompts(authorId);
    }
}


function openModal(prompt) {
    try {
        if (!prompt) {
            throw new Error('No prompt data available');
        }
        console.log('Opening modal for prompt:', prompt);

        document.getElementById('modal-title').textContent = prompt.name || 'Untitled';
        document.getElementById('modal-category').textContent = prompt.category || 'Uncategorized';
        document.getElementById('modal-description').textContent = prompt.description || '';
        document.getElementById('modal-prompt').textContent = prompt.original_prompt || '';
        
        // Initialize like button and count
        const loveButton = document.getElementById('love-button');
        const loveCount = document.getElementById('love-count');
        const heartIcon = loveButton.querySelector('i');
        
        // Set initial count
        loveCount.textContent = prompt.like_count || '0';
        
        // Check if user has already liked this prompt
        if (prompt.is_liked) {
            heartIcon.classList.remove('far');
            heartIcon.classList.add('fas');
            loveButton.disabled = true;
            loveButton.classList.add('opacity-50');
        } else {
            heartIcon.classList.remove('fas');
            heartIcon.classList.add('far');
            loveButton.disabled = false;
            loveButton.classList.remove('opacity-50');
        }
        
        // Add click handler
        loveButton.onclick = () => likePrompt(prompt.prompt_id);
        
        // Store prompt ID for customization
        const modalContent = document.getElementById('modal-content');
        if (modalContent) {
            modalContent.setAttribute('data-prompt-id', prompt.prompt_id);
        } else {
            console.error('Modal content element not found');
        }
        
        // Clear customization input
        document.getElementById('customization-input').value = '';
        
        promptModal.classList.remove('hidden');
        window.history.pushState({ promptId: prompt.prompt_id }, '', `?prompt_id=${prompt.prompt_id}`);
    } catch (error) {
        console.error('Error opening modal:', error);
        alert('Failed to load prompt details');
    }
}

function closeModal() {
    promptModal.classList.add('hidden');
    // Remove prompt_id from URL
    window.history.pushState({}, '', window.location.pathname);
}

function showLoading() {
    resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Loading...</div>';
}

function showError(message) {
    resultsGrid.innerHTML = `<div class="col-span-3 text-center text-white">${message}</div>`;
}

function resetToHome() {
    searchInput.value = '';
    // Show categories section again
    document.getElementById('categories-section').style.display = 'block';
    searchContainer.classList.add('justify-center');
    searchContainer.classList.remove('pt-8');
    resultsContainer.classList.add('hidden');
    currentCategory = null;
    currentSearchQuery = '';
    currentPage = 1;
    window.history.pushState({}, '', window.location.pathname);
}

// Share Modal Functions
function openShareModal() {
    shareModal.classList.remove('hidden');
}

function closeShareModal() {
    shareModal.classList.add('hidden');
}

// Share Functions
function shareViaEmail() {
    const prompt = document.getElementById('modal-prompt').textContent;
    const title = document.getElementById('modal-title').textContent;
    window.location.href = `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(prompt)}`;
}

function shareViaTwitter() {
    const title = document.getElementById('modal-title').textContent;
    const url = window.location.href;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`);
}

function shareViaLinkedIn() {
    const url = window.location.href;
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`);
}

function shareViaCopy() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        alert('Link copied to clipboard!');
    });
}

// Event Listeners
searchButton.addEventListener('click', performSearch);

searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

document.getElementById('share-button').addEventListener('click', openShareModal);
document.getElementById('upload-form').addEventListener('submit', handleUploadSubmit);

document.getElementById('customize-button').addEventListener('click', async () => {
    console.log('Customize button clicked');
    const modalContent1 = debugElement('modal-content');
    if (!modalContent1) {
        console.error('Modal content not found');
        alert('Error: Modal content not found');
        return;
    }
    const customization = document.getElementById('customization-input').value;
    if (customization.trim().length < 10) {
        alert('Please enter at least 10 characters for customization');
        return;
    }

    const button = document.getElementById('customize-button');
    const modalContent = document.getElementById('modal-content');
    
    if (!modalContent) {
        alert('Error: Modal content not found');
        return;
    }
    
    const promptId = modalContent.getAttribute('data-prompt-id');
    if (!promptId) {
        alert('Error: Prompt ID not found');
        return;
    }

    button.textContent = 'Customizing...';
    button.disabled = true;

    try {
        const customizedPrompt = await customizePrompt(promptId, customization);
        
        if (customizedPrompt) {
            document.getElementById('modal-prompt').textContent = customizedPrompt;
            document.getElementById('customization-input').value = '';
            
            // Show success message
            const successMessage = document.createElement('div');
            successMessage.className = 'text-green-500 text-sm mt-2';
            successMessage.textContent = 'Prompt customized successfully!';
            button.parentNode.insertBefore(successMessage, button.nextSibling);
            
            // Remove success message after 3 seconds
            setTimeout(() => successMessage.remove(), 3000);
        }
    } catch (error) {
        console.error('Customization failed:', error);
        alert('Failed to customize prompt: ' + (error.message || 'Unknown error'));
    } finally {
        button.textContent = 'Customize Prompt';
        button.disabled = false;
    }
});

document.getElementById('customization-input').addEventListener('input', function(e) {
    const minLength = 10;
    const maxLength = 1000;
    const value = e.target.value.trim();
    const remaining = maxLength - value.length;
    
    // Update character count
    const countElement = document.getElementById('char-count');
    countElement.textContent = `${value.length}/${maxLength} characters`;
    
    // Enable/disable customize button
    const customizeButton = document.getElementById('customize-button');
    customizeButton.disabled = value.length < minLength || value.length > maxLength;
    customizeButton.classList.toggle('opacity-100', !customizeButton.disabled);
    customizeButton.classList.toggle('cursor-not-allowed', customizeButton.disabled);
});

function toggleMenu() {
    const menu = document.getElementById('menu-dropdown');
    menu.classList.toggle('hidden');
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('menu-dropdown');
    const menuButton = event.target.closest('button');
    
    if (!menu.contains(event.target) && !menuButton?.onclick?.toString()?.includes('toggleMenu')) {
        menu.classList.add('hidden');
    }
});

function openUploadModal() {
    document.getElementById('upload-modal').classList.remove('hidden');
    document.getElementById('menu-dropdown').classList.add('hidden'); // Close menu when opening modal
}

function closeUploadModal() {
    document.getElementById('upload-modal').classList.add('hidden');
}


// Close modals when clicking outside
promptModal.addEventListener('click', (e) => {
    if (e.target === promptModal) closeModal();
});

shareModal.addEventListener('click', (e) => {
    if (e.target === shareModal) closeShareModal();
});

// Error handling for clipboard API
function handleClipboardError() {
    const copyButton = document.getElementById('copy-button');
    copyButton.textContent = 'Failed to copy';
    setTimeout(() => copyButton.textContent = 'Copy Prompt', 2000);
}

// Handle network errors
window.addEventListener('offline', () => {
    console.log('Network connection lost');
    // You can add UI feedback here
});

window.addEventListener('online', () => {
    console.log('Network connection restored');
    // You can add UI feedback here
});

function showCustomizationLoading() {
    const button = document.getElementById('customize-button');
    button.innerHTML = `
        <svg class="animate-spin h-5 w-5 mr-2 inline" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Customizing...
    `;
    button.disabled = true;
}

function hideCustomizationLoading() {
    const button = document.getElementById('customize-button');
    button.textContent = 'Customize Prompt';
    button.disabled = false;
}

function showCustomizationError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-red-500 text-sm mt-2';
    errorDiv.textContent = message;
    document.getElementById('customize-button').parentNode.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}