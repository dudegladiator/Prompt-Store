// API Endpoints (commented for future implementation)
/*
const API = {
    base: 'https://api.promptgenerator.com',
    search: '/api/prompts/search',      // GET: ?query=&category=&page=&pageSize=
    categories: '/api/categories',       // GET: Get all categories
    customize: '/api/prompts/customize', // POST: { promptId, customization }
}
*/

// Fake Data
const fakeCategories = [
    "Business Writing",
    "Creative Writing",
    "Programming",
    "Marketing",
    "Career Development"
];

const fakePrompts = [
    {
        id: 1,
        title: "Professional Email Writer",
        description: "1AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "2AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "3AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "4AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "9AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "10AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 1,
        title: "Professional Email Writer",
        description: "AI prompt for writing professional and effective emails",
        category: "Business Writing",
        prompt: "I want you to act as a professional email writer. Write a clear and concise email that maintains a professional tone while effectively communicating the message. Consider the recipient's perspective and ensure proper email etiquette."
    },
    {
        id: 2,
        title: "Story Generator",
        description: "Creates unique short stories based on given elements",
        category: "Creative Writing",
        prompt: "You are a creative story generator. Create an engaging short story incorporating the following elements: mystery, surprise ending, and character development. The story should be original and captivating."
    },
    {
        id: 3,
        title: "Code Reviewer",
        description: "Technical prompt for code review and optimization",
        category: "Programming",
        prompt: "Act as a senior software engineer conducting a code review. Analyze the code for best practices, potential bugs, security issues, and suggest optimizations while maintaining code readability and performance."
    },
    {
        id: 4,
        title: "Marketing Copy Expert",
        description: "Creates compelling marketing content",
        category: "Marketing",
        prompt: "You are an expert marketing copywriter. Create compelling marketing copy that engages the target audience, highlights key benefits, and includes a strong call-to-action while maintaining brand voice."
    },
    {
        id: 5,
        title: "Interview Coach",
        description: "Helps prepare for job interviews",
        category: "Career Development",
        prompt: "Act as an interview coach preparing a candidate for a job interview. Provide strategic answers to common interview questions, body language tips, and guidance on presenting professional experience effectively."
    }
    // Add more fake prompts as needed
];

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
function initializeCategories() {
    fakeCategories.forEach(category => {
        const button = document.createElement('button');
        button.className = 'px-4 py-2 text-sm text-white bg-zinc-900 rounded-full hover:bg-zinc-800 focus:outline-none';
        button.textContent = category;
        button.addEventListener('click', () => searchByCategory(category));
        categoriesContainer.appendChild(button);
    });
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
    if (!query) return; // Don't proceed if query is empty

    currentSearchQuery = query;
    currentCategory = null;
    currentPage = 1;
    
    // Hide categories section completely
    document.getElementById('categories-section').style.display = 'none';
    
    // Move search bar up
    searchContainer.classList.remove('justify-center');
    searchContainer.classList.add('pt-8');
    
    // Show results container
    resultsContainer.classList.remove('hidden');
    
    try {
        // Show loading state
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Searching...</div>';
        
        // Simulate API call
        const results = await fakeSearchAPI(query, currentPage, pageSize);
        
        // Display results
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
    
    // Hide categories section
    document.getElementById('categories-section').style.display = 'none';
    
    searchContainer.classList.remove('justify-center');
    searchContainer.classList.add('pt-8');
    resultsContainer.classList.remove('hidden');

    try {
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Loading...</div>';
        const results = await fakeSearchAPI('', currentPage, pageSize, category);
        displayResults(results);
    } catch (error) {
        console.error('Category search error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred</div>';
    }
}

// Fake API Calls
async function fakeSearchAPI(query, page, pageSize, category = null) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    let filtered = [...fakePrompts];
    
    // Filter by search query
    if (query) {
        const searchTerm = query.toLowerCase();
        filtered = filtered.filter(p => 
            p.title.toLowerCase().includes(searchTerm) ||
            p.description.toLowerCase().includes(searchTerm) ||
            p.prompt.toLowerCase().includes(searchTerm)
        );
    }

    // Filter by category
    if (category) {
        filtered = filtered.filter(p => p.category === category);
    }

    // Calculate pagination
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedItems = filtered.slice(startIndex, endIndex);

    return {
        items: paginatedItems,
        totalPages: Math.ceil(filtered.length / pageSize),
        currentPage: page,
        totalItems: filtered.length
    };
}

async function fakeCustomizeAPI(promptData, customization) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    return {
        ...promptData,
        prompt: `${promptData.prompt}\n\nCustomized with: ${customization}`
    };
}

// Handle Page Change
async function handlePageChange(page) {
    currentPage = page;
    let results;
    
    try {
        if (currentSearchQuery) {
            results = await fakeSearchAPI(currentSearchQuery, currentPage, pageSize);
        } else if (currentCategory) {
            results = await fakeSearchAPI('', currentPage, pageSize, currentCategory);
        } else {
            results = await fakeSearchAPI('', currentPage, pageSize);
        }
        
        displayResults(results);
        window.scrollTo(0, 0);
    } catch (error) {
        console.error('Page change error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred</div>';
    }
}

// Display Functions
function displayResults(results) {
    resultsGrid.innerHTML = ''; // Clear existing results
    
    results.items.forEach(prompt => {
        const card = document.createElement('div');
        card.className = 'bg-zinc-900 rounded-lg p-6 cursor-pointer hover:bg-zinc-800 transition-colors';
        card.innerHTML = `
            <h3 class="text-xl font-semibold text-white mb-2">${prompt.title}</h3>
            <p class="text-gray-400 mb-2">${prompt.description}</p>
            <span class="inline-block px-3 py-1 text-sm text-white bg-zinc-800 rounded-full">${prompt.category}</span>
        `;
        card.addEventListener('click', () => openModal(prompt));
        resultsGrid.appendChild(card);
    });

    // Only show pagination if total items exceed page size
    paginationContainer.innerHTML = '';
    if (results.totalItems > pageSize) {
        displayPagination(results.totalPages);
    }
}

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

// URL and Modal Functions
function findPromptById(id) {
    return fakePrompts.find(p => p.id === parseInt(id));
}

function checkUrlForPrompt() {
    const urlParams = new URLSearchParams(window.location.search);
    const promptId = urlParams.get('prompt_id');
    
    if (promptId) {
        const prompt = findPromptById(parseInt(promptId));
        if (prompt) {
            openModal(prompt);
        }
    }
}

// Add this new function for "View All Prompts"
async function viewAllPrompts() {
    currentCategory = null;
    currentSearchQuery = '';
    currentPage = 1;
    searchInput.value = '';
    
    // Hide categories section
    document.getElementById('categories-section').style.display = 'none';
    
    searchContainer.classList.remove('justify-center');
    searchContainer.classList.add('pt-8');
    resultsContainer.classList.remove('hidden');

    try {
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">Loading...</div>';
        const results = await fakeSearchAPI('', currentPage, pageSize);
        displayResults(results);
    } catch (error) {
        console.error('View all prompts error:', error);
        resultsGrid.innerHTML = '<div class="col-span-3 text-center text-white">An error occurred</div>';
    }
}

function openModal(prompt) {
    document.getElementById('modal-title').textContent = prompt.title;
    document.getElementById('modal-category').textContent = prompt.category;
    document.getElementById('modal-description').textContent = prompt.description;
    document.getElementById('modal-prompt').textContent = prompt.prompt;
    promptModal.classList.remove('hidden');
    
    // Update URL
    const newUrl = `${window.location.pathname}?prompt_id=${prompt.id}`;
    window.history.pushState({ promptId: prompt.id }, '', newUrl);
}

function closeModal() {
    promptModal.classList.add('hidden');
    // Remove prompt_id from URL
    window.history.pushState({}, '', window.location.pathname);
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

document.getElementById('customize-button').addEventListener('click', async () => {
    const customization = document.getElementById('customization-input').value;
    if (customization.trim()) {
        const button = document.getElementById('customize-button');
        button.textContent = 'Customizing...';
        button.disabled = true;

        try {
            const currentPrompt = {
                title: document.getElementById('modal-title').textContent,
                category: document.getElementById('modal-category').textContent,
                description: document.getElementById('modal-description').textContent,
                prompt: document.getElementById('modal-prompt').textContent
            };

            const customizedPrompt = await fakeCustomizeAPI(currentPrompt, customization);
            
            document.getElementById('modal-prompt').textContent = customizedPrompt.prompt;
            document.getElementById('customization-input').value = '';
        } catch (error) {
            console.error('Customization error:', error);
            alert('An error occurred while customizing the prompt');
        } finally {
            button.textContent = 'Customize Prompt';
            button.disabled = false;
        }
    }
});

// Handle browser back/forward buttons
window.addEventListener('popstate', (event) => {
    const urlParams = new URLSearchParams(window.location.search);
    const promptId = urlParams.get('prompt_id');
    
    if (promptId) {
        const prompt = findPromptById(parseInt(promptId));
        if (prompt) {
            openModal(prompt);
        }
    } else {
        closeModal();
    }
});

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
