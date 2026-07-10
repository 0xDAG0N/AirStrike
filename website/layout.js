(() => {
    const headerTemplate = (slot = '') => {
        const trimmedSlot = slot.trim();
        const hero = trimmedSlot ? `\n${trimmedSlot}\n` : '\n';
        return `<header class="bg-cover">
    <nav class="container">
        <a id="logo" href="/" style="background-image:url(/images/airstrike-logo-white.svg)"></a>
        <ul id="navigation">
            
            <li>
                <a href="https://github.com/mahmoud-sadder/airstrike/archive/refs/tags/v0.0.zip">Get Airstrike</a>
            </li>
            <li class="dropdown-menu">
                <span>Documentation <i class="ti-angle-down">
      </i>
    </span>
                <div>
                    <a href="/docs/">Documentation Pages</a>
                    <a href="/attacks/">Attacks Documentation</a>
                    <a href="/faq/">Frequently Asked Questions</a>
                    <a href="https://github.com/mahmoud-sadder/airstrike/issues">Known Issues</a>
                </div>
            </li>
            <li class="dropdown-menu">
                
                <span>Developers <i class="ti-angle-down">
  </i>
</span>
                <div>
                    <a href="https://github.com/mahmoud-sadder/airstrike">Git Repositories</a>
                    
                </div>
            </li>
            <li class="dropdown-menu">
                <span>About <i class="ti-angle-down">
</i>
</span>
                <div>
                    <a href="/features/">Airstrike Overview</a>
                    <a href="/about-us/">Meet The Airstrike Team</a>
                    <a href="/partnerships/">Partnerships</a>
                    <a href="/contact/">Contact Us</a>
                </div>
            </li>
        </ul>
        <button title="show menu">
            <div>
            </div>
            <div>
            </div>
            <div>
            </div>
        </button>
    </nav>${hero}</header>`;
    };

    const footerTemplate = `<footer>
    <div class="container footer-nav">
        <div>
            <h4>General</h4>
            <a href="/" rel="noopener" target="_blank">Home</a>
            <a href="https://github.com/mahmoud-sadder/airstrike/archive/refs/tags/v0.0.zip" rel="noopener" target="_blank">Get Airstrike</a>
        </div>
        <div>
            <h4>Documentation</h4>
            <a href="/docs/" rel="noopener" target="_blank">Documentation Pages</a>
            <a href="/attacks/" rel="noopener" target="_blank">Attacks Documentation</a>
            <a href="/faq/" rel="noopener" target="_blank">Frequently Asked Questions</a>
            <a href="https://github.com/mahmoud-sadder/airstrike/issues" rel="noopener" target="_blank">Known Issues</a>
        </div>
        <div>
            <h4>Developers</h4>
            <a href="https://github.com/mahmoud-sadder/airstrike" rel="noopener" target="_blank">Git Repositories</a>
        </div>
        <div>
            <h4>About</h4>
            <a href="/features/" rel="noopener" target="_blank">Airstrike Overview</a>
            <a href="/about-us/" rel="noopener" target="_blank">Meet The Airstrike Team</a>
            <a href="/partnerships/" rel="noopener" target="_blank">Partnerships</a>
            <a href="/contact/" rel="noopener" target="_blank">Contact Us</a>
        </div>
        <div>
            <img id="footer-logo" src="/images/airstrike-jet-logo-white-transperant.svg" alt="Airstrike jet logo" />
            &copy; Airstrike Services Limited 2025. All rights reserved.
        </div>
    </div>
    <div class="darkmode-switch">
        LIGHT
        <label class="switch" title="Toggle light and dark theme">
            <input type="checkbox" name="toggle-darkmode" aria-label="Toggle light and dark theme" checked>
            <div></div>
        </label>
        DARK
    </div>
</footer>`;
const collectHeaderTargets = () => {
        const explicitPlaceholders = [...document.querySelectorAll('[data-template="site-header"]')];
        if (explicitPlaceholders.length) {
            return explicitPlaceholders.map((node) => ({
                node,
                slot: node.innerHTML || ''
            }));
        }

        const fallbackHeader = document.querySelector('header');
        if (!fallbackHeader) {
            return [];
        }

        return [{
            node: fallbackHeader,
            slot: ''
        }];
    };

    const collectFooterTargets = () => {
        const explicitPlaceholders = [...document.querySelectorAll('[data-template="site-footer"]')];
        if (explicitPlaceholders.length) {
            return explicitPlaceholders;
        }

        const fallbackFooter = document.querySelector('footer');
        return fallbackFooter ? [fallbackFooter] : [];
    };

    const applyTemplates = () => {
        collectHeaderTargets().forEach(({ node, slot }) => {
            node.outerHTML = headerTemplate(slot);
        });

        collectFooterTargets().forEach((node) => {
            node.outerHTML = footerTemplate;
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyTemplates);
    } else {
        applyTemplates();
    }
})();
