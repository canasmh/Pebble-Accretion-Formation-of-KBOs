from pandas import read_csv as csv
import numpy as np


class StreamingInstabilityData:

    def __init__(self, rho_ice, rho_sil, unit_mass, initial_porosity=0.5, file_path="./data/si-data.csv"):

        self.rho_ice = rho_ice  # Density of icy pebbles
        self.rho_sil = rho_sil  # Density of silicate pebbles
        self.file_path = file_path  # File path to the CSV file
        self.unit_mass = unit_mass  # Actual gas mass contained in one cubic scale height
        self.initial_porosity = initial_porosity  # Initial porosity of KBOs

        # The following parameters are from the simulation -- required to convert to physical units
        self.npar = 1.536e7  # Number of particles used in the simulation
        self.eps = 0.03  # Dust to gas ratio
        self.total_density = 16749076.820152447  # Sum of the gas density in our simulation (code units)
        self.dx, self.dy, self.dz = (0.00078125, 0.00078125, 0.00078125)  # Grid spacing in out simulation
        self.__get_planetesimal_properties()

    def __read_data(self):
        data = csv(self.file_path)
        
        return data.n_ice, data.n_sil

    def __get_planetesimal_properties(self):
        n_ice, n_sil = self.__read_data()
        self.n_mass = len(n_ice)
        self.porosity = np.repeat(self.initial_porosity, self.n_mass)
        mgas_code = self.total_density * self.dx * self.dy * self.dz  # Sum of the gas mass in our simulation (code units)
        mpar_code = mgas_code * self.eps / self.npar
        mpar = mpar_code * self.unit_mass

        self.ice_fraction = np.array([n_ice[i] / (n_ice[i] + n_sil[i]) for i in range(self.n_mass)])
        self.mass = np.array([(n_ice[i] + n_sil[i]) * mpar for i in range(self.n_mass)])
        self.density = np.array([self.porosity[i] * ((self.rho_ice * self.ice_fraction[i]) + (self.rho_sil * (1 - self.ice_fraction[i]))) for i in range(self.n_mass)])
    
    def add_masses(self, n_bins, m_per_bin, min_dens, max_dens, min_mass, max_mass):
        masses_to_add = np.linspace(min_mass, max_mass, n_bins)
        added_masses_final = []
        added_density_final = []
        added_ice_frac_final = []
        for _ in range(m_per_bin):
            for j in range(n_bins):
                new_mass = masses_to_add[j]
                new_density = min_dens + np.random.rand() * (max_dens - min_dens)
                new_ice_fraction = (new_density - self.rho_sil * self.initial_porosity) / ((self.rho_ice - self.rho_sil) * self.initial_porosity)
                added_masses_final += [new_mass]
                added_density_final += [new_density]
                added_ice_frac_final += [new_ice_fraction]
        
        self.ice_fraction = np.array(list(self.ice_fraction) + added_ice_frac_final)
        self.mass = np.array(list(self.mass) + added_masses_final)
        self.density = np.array(list(self.density) + added_density_final)
        self.porosity = np.array(list(self.porosity) + [0.5] * (n_bins * m_per_bin))
        self.n_mass += (m_per_bin * n_bins)

    def radius(self, i=None):
        if i is None:
            return (3 * self.mass / (4 * np.pi * self.density)) ** (1 / 3)
        else:
            return (3 * self.mass[i] / (4 * np.pi * self.density[i])) ** (1 / 3)

class KuiperBeltData:

    def __init__(self, file_path="./data/kbo-data.csv"):
        self.file_path = file_path
        self.__read_data()

    def __read_data(self):
        data = csv(self.file_path)
        self.density = data["Density"]
        self.radius = data["Diameter"] / 2 * 1e5
        self.mass = self.density * 4 / 3 * np.pi * self.radius ** 3
        self.min_radius = (data["Diameter"] - data["MinusDiameter"]) / 2 * 1e5
        self.max_radius = (data["Diameter"] + data["PlusDiameter"]) / 2 * 1e5
        self.min_density = self.density - self.mass / ( 4 / 3 * np.pi * self.max_radius ** 3)
        self.max_density = self.mass / ( 4 / 3 * np.pi * self.min_radius ** 3) - self.density


if __name__ == "__main__":
    from constants import M_PLUTO
    import matplotlib.pyplot as plt

    kbos = StreamingInstabilityData(rho_ice=1, rho_sil=3.5, unit_mass=2.823973078884959e+28)
    kbos.add_masses(n_bins=50, m_per_bin=3, min_dens=min(kbos.density), max_dens=max(kbos.density), min_mass=1e-3 * M_PLUTO, max_mass=1e-2 * M_PLUTO)
    real_kbos = KuiperBeltData()


    plt.figure(figsize=(7,5))
    plt.scatter(kbos.mass / M_PLUTO, kbos.density, c=kbos.ice_fraction * 100, vmin=0, vmax=100)
    plt.scatter(real_kbos.mass / M_PLUTO, real_kbos.density, marker="*", s=15 ** 2, c="r", zorder=5)
    plt.errorbar(x=real_kbos.mass / M_PLUTO, y=real_kbos.density, yerr=[real_kbos.min_density, real_kbos.max_density], ls='none', ecolor='k')
    plt.xscale('log')
    plt.xlabel(r'Mass (M$_{\rm{Pluto}})$')
    plt.ylabel(r'Density (g cm$^{-3}$)')
    plt.xlim(5e-5, 2.5)
    plt.ylim(0, 3)
    plt.show()
