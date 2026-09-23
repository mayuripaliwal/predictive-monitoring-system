import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/react'
import { Bars3Icon, XMarkIcon,PlusIcon } from '@heroicons/react/24/outline'
import {NavLink} from 'react-router-dom';
export default function Navbar() {
  return (
    <Disclosure
      as="nav"
      className="relative bg-white max-w-full "
    >
      <div className="mx-auto max-w-full px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex">
            <div className="mr-2 -ml-2 flex items-center md:hidden">
              {/* Mobile menu button */}
              <DisclosureButton className="group relative inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:ring-2 focus:ring-green-600 focus:outline-hidden focus:ring-inset ">
                <span className="absolute -inset-0.5" />
                <span className="sr-only">Open main menu</span>
                <Bars3Icon aria-hidden="true" className="block size-6 group-data-open:hidden" />
                <XMarkIcon aria-hidden="true" className="hidden size-6 group-data-open:block" />
              </DisclosureButton>
            </div>
            <div className="hidden md:ml-6 md:flex md:space-x-8">
              <NavLink
                to='/monitors'
                className={({isActive})=>`inline-flex items-center border-b-2 px-1 pt-1 text-xl font-medium
                 text-gray-500 ${isActive?'border-green-600 text-gray-900':'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
              >
                Monitors
              </NavLink>
              <NavLink
                to='/create-monitor'
                className={({isActive})=>`inline-flex items-center border-b-2 px-1 pt-1 text-xl font-medium
                 text-gray-500 ${isActive?'border-green-600 text-gray-900':'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
              >
                Create a monitor
              </NavLink>
            </div>
          </div>
        </div>
      </div>

      <DisclosurePanel className="md:hidden">
        <div className="space-y-1 pt-2 pb-3">
          {/* Current: "bg-green-50 border-green-600 text-green-700 dark:border-green-500 dark:bg-green-600/10 dark:text-green-400", Default: "border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800 dark:hover:border-white/20 dark:hover:bg-white/5 dark:hover:text-white" */}
          <DisclosureButton
            as="a"
            href="#about"
            className="block border-l-4 border-green-600 bg-green-50 py-2 pr-4 pl-3 text-base font-medium text-green-700 sm:pr-6 sm:pl-5 dark:border-green-500 dark:bg-green-600/10 dark:text-green-400"
          >
            About
          </DisclosureButton>
          <DisclosureButton
            as="a"
            href="#projects"
            className="block border-l-4 border-transparent py-2 pr-4 pl-3 text-base font-medium text-gray-500 hover:border-gray-300 hover:bg-gray-50 hover:text-gray-800 sm:pr-6 sm:pl-5 dark:text-gray-300 dark:hover:border-white/20 dark:hover:bg-white/5 dark:hover:text-white"
          >
            Projects
          </DisclosureButton>
        </div>
      </DisclosurePanel>
    </Disclosure>
  )
}
