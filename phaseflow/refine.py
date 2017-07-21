import fenics
import numpy


solution_at_point = numpy.array([1.e32, 1.e32, 1.e32, 1.e32, 1.e32], dtype=numpy.float_) # Oversized for up to 3D

def mark_pci_cells(regularization, mesh, w):

    hot = (regularization['theta_s'] + 2*regularization['R_s'] - fenics.dolfin.DOLFIN_EPS)
            
    cold = (regularization['theta_s'] - 2*regularization['R_s'] + fenics.dolfin.DOLFIN_EPS)

    contains_pci = fenics.CellFunction("bool", mesh)

    contains_pci.set_all(False)

    for cell in fenics.cells(mesh):
        
        hot_vertex_count = 0
        
        cold_vertex_count = 0
        
        for vertex in fenics.vertices(cell):
        
            w.eval_cell(solution_at_point, numpy.array([vertex.x(0), vertex.x(1), vertex.x(2)]), cell) # Works for 1/2/3D
            
            theta = solution_at_point[mesh.type().dim() + 1]
            
            if theta > hot:
            
                hot_vertex_count += 1
                
            if theta < cold:
            
                cold_vertex_count += 1

        if (0 < hot_vertex_count < 1 + mesh.type().dim()) | (0 < cold_vertex_count < 1 + mesh.type().dim()):
        
            contains_pci[cell] = True
                
    return contains_pci