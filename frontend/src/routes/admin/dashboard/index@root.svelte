<script context="module">
	export async function load({ session, fetch }) {
		if (!session) {
			return {
				status: 302,
				redirect: '/login'
			}
		}
		if (session?.status === 'admin') {
			// FETCH DETAILS HERE /api/v1/admin/clinics
			const res = await fetch(ENV.VITE_FINDCARE_API_BASE_URL + '/api/v1/admin/clinics', {
				method: 'GET',
				headers: {
					'Content-type': 'application/json',
					Authorization: `Bearer ${session.session}`
				}
			})
			const resp = await fetch(ENV.VITE_FINDCARE_API_BASE_URL + '/api/v1/admin/users', {
				method: 'GET',
				headers: {
					'Content-type': 'application/json',
					Authorization: `Bearer ${session.session}`
				}
			})
			const users = await resp.json()
			const data = await res.json()
			let u = null
			let c = null
			if (res.ok) {
				c = data
			}
			if (resp.ok) {
				u = users
			}
			return {
				props: {
					users: u,
					clinics: c
				}
			}
		} else {
			if (session?.status === 'doctor') {
				return {
					status: 302,
					redirect: '/doctor'
				}
			} else {
				return {
					status: 302,
					redirect: '/profile'
				}
			}
		}
	}
</script>

<script>
	import Footer from '$lib/components/dashboard-footer.svelte'
	import UserTable from '$lib/components/admin/UserTable.svelte'
	import Changepass from '$lib/components/Changepass.svelte'
	import Header from '$lib/components/admin/Header.svelte'
	import DoctorTable from '$lib/components/admin/DoctorTable.svelte'
	import AccountSetting from '$lib/components/admin/AccountSetting.svelte'
	import AddUser from '$lib/components/admin/AddUser.svelte'
	import AddDoctor from '$lib/components/admin/AddDoctor.svelte'
	import { ENV } from '$lib/utils'
	import SearchSort from '$lib/components/Search-Sort.svelte'
	import { session } from '$app/stores'
	import {
		user as userProfileStore,
		adminQueryDoctorName,
		adminQueryUserEmail
	} from '../../../stores'
	export let clinics, users
	function toggleCollapseShow(classes) {
		collapseShow = classes
	}
	let collapseShow = 'hidden'
	let show = false
	let selected = 'dashboard'
	let accountSettingJson
	let filteredUserList = []
	let filteredDoctorList = []
	let is_account_setting_loading = false
	let is_dashboard_loading = false
	const accountSettingHandler = async () => {
		is_account_setting_loading = true
		const res = await fetch(ENV.VITE_FINDCARE_API_BASE_URL + '/api/v1/admin/', {
			method: 'GET',
			headers: {
				'Content-type': 'application/json',
				//@ts-ignore
				Authorization: `Bearer ${$session.session}`
			}
		})
		const data = await res.json()
		accountSettingJson = data
		is_account_setting_loading = false
		selected = 'Account Setting'
	}

	const dashboardHandler = async () => {
		is_dashboard_loading = true
		const res = await fetch(ENV.VITE_FINDCARE_API_BASE_URL + '/api/v1/admin/clinics', {
			method: 'GET',
			headers: {
				'Content-type': 'application/json',
				//@ts-ignore
				Authorization: `Bearer ${$session.session}`
			}
		})
		const resp = await fetch(ENV.VITE_FINDCARE_API_BASE_URL + '/api/v1/admin/users', {
			method: 'GET',
			headers: {
				'Content-type': 'application/json',
				//@ts-ignore
				Authorization: `Bearer ${$session.session}`
			}
		})
		const users_temp = await resp.json()
		const clinics_temp = await res.json()
		is_dashboard_loading = false
		if (res.ok) {
			clinics = clinics_temp
		} else {
			clinics = null
		}
		if (resp.ok) {
			users = users_temp
		} else {
			users = null
		}
		selected = 'dashboard'
	}

	$: if ($adminQueryUserEmail && users) {
		filteredUserList = users.filter((data) =>
			data.email.toLowerCase().startsWith($adminQueryUserEmail.toLowerCase())
		)
	} else {
		if (users) filteredUserList = [...users]
	}
	$: if ($adminQueryDoctorName && clinics) {
		filteredDoctorList = clinics.filter((data) => {
			const fullName = data.doctor.name.toLowerCase()
			const reversedFullName = fullName.split('').reverse().join('').toLowerCase()
			const trimmedSearchValue = $adminQueryDoctorName.toLowerCase()
			return fullName.includes(trimmedSearchValue) || reversedFullName.includes(trimmedSearchValue)
		})
	} else {
		if (clinics) filteredDoctorList = [...clinics]
	}
</script>

<svelte:head>
	<title>Admin Dashboard</title>
</svelte:head>
<div class="h-screen w-screen overflow-x-hidden font-maven">
	<!-- Sidebar -->

	<nav
		class="md:left-0 md:block md:fixed md:top-0 md:bottom-0 md:overflow-y-auto md:flex-row md:flex-nowrap md:overflow-hidden shadow-xl bg-white flex flex-wrap items-center justify-between relative md:w-64 z-10 py-4 px-6"
	>
		<div
			class="md:flex-col md:items-stretch md:min-h-full md:flex-nowrap px-0 flex flex-wrap items-center justify-between w-full mx-auto"
		>
			<!-- Toggler -->
			<button
				class="cursor-pointer text-black opacity-50 md:hidden px-3 py-1 text-xl leading-none bg-transparent rounded border border-solid border-transparent"
				type="button"
				on:click={() => toggleCollapseShow('bg-white m-2 py-3 px-6')}
			>
				<i class="fas fa-bars" />
			</button>
			<!-- Brand -->
			<a
				class="md:block text-left md:pb-2 text-blueGray-600 mr-0 inline-block whitespace-nowrap text-sm uppercase font-bold p-4 px-0"
				href="/"
			>
				<div class="p-2 text-primary text-3xl font-bold tracking-wide font-poppins">
					<a href="/">Find<span class="text-[#fb3434]">Care</span></a>
				</div>
			</a>
			<!-- User -->
			<ul class="md:hidden items-center flex flex-wrap list-none">
				<li class="inline-block relative" />
				<li class="inline-block relative" />
			</ul>
			<!-- Collapse -->
			<div
				class="md:flex md:flex-col md:items-stretch md:opacity-100 md:relative md:mt-4 md:shadow-none shadow absolute top-0 left-0 right-0 z-40 overflow-y-auto overflow-x-hidden h-auto items-center flex-1 rounded {collapseShow}"
			>
				<!-- Collapse header -->
				<div
					class="md:min-w-full md:hidden block pb-4 mb-4 border-b border-solid border-blueGray-200"
				>
					<div class="flex flex-wrap">
						<div class="w-6/12">
							<a
								class="md:block text-left md:pb-2 text-blueGray-600 mr-0 inline-block whitespace-nowrap text-sm uppercase font-bold p-2 px-0"
								href="/"
							>
								<div class=" text-primary text-3xl font-bold tracking-wide font-poppins">
									<a href="/">Find<span class="text-[#fb3434]">Care</span></a>
								</div>
							</a>
						</div>
						<div class="w-6/12 flex justify-end">
							<button
								type="button"
								class="cursor-pointer text-black opacity-50 md:hidden px-3 py-1 text-xl leading-none bg-transparent rounded border border-solid border-transparent"
								on:click={() => toggleCollapseShow('hidden')}
							>
								<i class="fas fa-times" />
							</button>
						</div>
					</div>
				</div>
				<!-- Divider -->
				<hr class="mb-4 md:min-w-full" />
				<!-- Heading -->
				<h6
					class="md:min-w-full text-blueGray-500 text-xs uppercase font-bold block pt-1 pb-4 no-underline"
				>
					Admin Layout Pages
				</h6>
				<!-- Navigation -->

				<ul class="md:flex-col md:min-w-full flex flex-col list-none">
					<li class="items-center">
						<button class="text-xs uppercase py-3 font-bold block  " on:click={dashboardHandler}>
							<i
								class="{is_dashboard_loading
									? 'loading fa fa-spinner fa-spin ml-2 mr-2'
									: 'fas fa-tv ml-2 mr-2'} text-sm text-primary "
							/>
							Dashboard
						</button>
						{#if selected == 'dashboard'}
							<hr class="border-[1px] border-primary bg-primary" />
						{/if}
					</li>

					<li class="items-center">
						<button
							class="text-blueGray-700 hover:text-blueGray-500 text-xs uppercase py-3 font-bold block"
							on:click={accountSettingHandler}
						>
							<i
								class="{is_account_setting_loading
									? 'loading fa fa-spinner fa-spin'
									: 'fas fa-user-circle'} text-primary ml-2 mr-2 text-sm"
							/>
							Account Setting
						</button>
						{#if selected == 'Account Setting'}
							<hr class="border-[1px] border-primary bg-primary" />
						{/if}
					</li>
					<li class="items-center">
						<button
							class="text-xs uppercase py-3 font-bold block"
							on:click={() => (selected = 'adduser')}
						>
							<i class="fas fa-user-plus ml-2 mr-2 text-sm text-primary " />
							Add User
						</button>
						{#if selected == 'adduser'}
							<hr class="border-[1px] border-primary bg-primary" />
						{/if}
					</li>
					<li class="items-center">
						<button
							class="text-xs uppercase py-3 font-bold block"
							on:click={() => (selected = 'adddoctor')}
						>
							<i class="fas fa-hospital-user ml-2 mr-2 text-sm text-primary" />
							Add Doctor
						</button>
						{#if selected == 'adddoctor'}
							<hr class="border-[1px] border-primary bg-primary" />
						{/if}
					</li>
					<li class="items-center">
						<button
							class="text-xs uppercase py-3 font-bold block "
							on:click={() => (selected = 'changepass')}
						>
							<i class="fas fa-key ml-2 mr-2 text-sm text-primary" />
							Change Password
						</button>
						{#if selected == 'changepass'}
							<hr class="border-[1px] border-primary bg-primary" />
						{/if}
					</li>
					<li class="items-center">
						<button
							class="text-xs uppercase py-3 font-bold block "
							on:click={async () => {
								$session = null
								$userProfileStore = null
								await fetch('../../api/v1/auth/logout')
							}}
						>
							<i class="fas fa-arrow-right-from-bracket ml-2 mr-2 text-sm text-primary" />
							Logout
						</button>
					</li>
				</ul>

				<!-- Divider -->
				<hr class="my-4 md:min-w-full" />
			</div>
		</div>
	</nav>

	<!-- Body -->

	<div class="relative md:ml-64 bg-blueGray-100 font-maven">
		<Header {clinics} />
		<div class="px-4 md:px-10 mx-auto w-full m-24 mt-3">
			{#if selected == 'dashboard'}
				{#if users}
					<SearchSort placeholderdata="Search User By Email" type="user" />
					<UserTable users={filteredUserList} />
				{/if}
				<hr class="my-12" />
				{#if clinics}
					<SearchSort placeholderdata="Search Doctor By Name" type="doctor" />
					<DoctorTable clinics={filteredDoctorList} />
				{/if}
			{/if}
			{#if selected == 'Account Setting'}
				<AccountSetting {accountSettingJson} />
			{/if}
			{#if selected == 'changepass'}
				<Changepass isAdmin={true} />
			{/if}
			{#if selected == 'adduser'}
				<AddUser />
			{/if}
			{#if selected == 'adddoctor'}
				<AddDoctor />
			{/if}

			<Footer />
		</div>
	</div>
</div>
